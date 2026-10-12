# Run from the heor-rwe directory. Install survey and jsonlite first.
suppressPackageStartupMessages(library(survey))
suppressPackageStartupMessages(library(jsonlite))
options(survey.lonely.psu = "fail", survey.adjust.domain.lonely = FALSE)
p <- read.csv("data/processed/persons.csv", colClasses=c(DUPERSID="character"))
p <- p[p$PERWT24F > 0, ]
stopifnot(!anyNA(p), all(p$VARSTR > 0), all(p$VARPSU > 0))
psus <- unique(p[c("VARSTR", "VARPSU")])
stopifnot(all(table(psus$VARSTR) >= 2))
design <- svydesign(ids=~VARPSU, strata=~VARSTR, weights=~PERWT24F, nest=TRUE, data=p)
adult <- subset(design, AGELAST >= 18)

# Independent ratio linearization over FULL design (zero contributions outside domain).
# This checks survey SEs, including domains with only one contributing PSU.
manual_ratio <- function(numerator, denominator) {
  w <- p$PERWT24F
  estimate <- sum(w * numerator) / sum(w * denominator)
  linearized <- w * (numerator - estimate * denominator) / sum(w * denominator)
  totals <- aggregate(linearized, p[c("VARSTR", "VARPSU")], sum)
  variances <- tapply(totals$x, totals$VARSTR, function(z) length(z) * var(z))
  c(estimate=estimate, se=sqrt(sum(variances)))
}

rows <- list()
checks <- 0L
add_row <- function(drug, population, insurance, metric, n, users, estimate, se, ci, df) {
  estimate <- as.numeric(estimate); se <- as.numeric(se); ci <- as.numeric(ci)
  rse <- if (estimate != 0) abs(se/estimate) else Inf
  reason <- if (n < 100) "suppressed: adult n < 100" else if (users < 30) "suppressed: user n < 30" else if (df < 1) "suppressed: design df < 1" else if (!is.finite(rse) || rse > .30) "suppressed: RSE > 30%" else "reportable"
  rows[[length(rows)+1]] <<- data.frame(drug, population, insurance, metric,
    unweighted_adults=n, unweighted_users=users,
    estimate=if(reason=="reportable") estimate else NA_real_,
    se=if(reason=="reportable") se else NA_real_,
    lower_95=if(reason=="reportable") ci[1] else NA_real_,
    upper_95=if(reason=="reportable") ci[2] else NA_real_,
    rse=if(reason=="reportable") rse else NA_real_, design_df=df, status=reason)
}

for (drug in c("primary", "semaglutide", "tirzepatide", "brand")) {
  prefix <- if(drug=="primary") "" else paste0(drug,"_")
  v <- paste0(prefix, c("user","oop","total","fills"))
  age_groups <- if(drug=="primary") c("All adults", "18-64", "65+") else "All adults"
  for (age_group in age_groups) {
    age_mask <- p$AGELAST >= 18
    if(age_group=="18-64") age_mask <- age_mask & p$AGELAST < 65
    if(age_group=="65+") age_mask <- age_mask & p$AGELAST >= 65
    insurance_groups <- if(drug=="primary") 0:3 else 0
    for (ins in insurance_groups) {
      mask <- age_mask & (ins==0 | p$INSCOV24==ins)
      ins_label <- c("All coverage", "Any private incl. TRICARE", "Public only", "Uninsured all year")[ins+1]
      d <- design[mask, ]
      n <- sum(mask); u <- sum(mask & p[[v[1]]] == 1)
      user_mask <- mask & p[[v[1]]] == 1
      du <- design[user_mask, ]
      prev <- svymean(reformulate(v[1]), d)
      manual <- manual_ratio(p[[v[1]]] * mask, as.numeric(mask))
      stopifnot(isTRUE(all.equal(as.numeric(coef(prev)), manual[[1]], tolerance=1e-8)),
                isTRUE(all.equal(as.numeric(SE(prev)), manual[[2]], tolerance=1e-8)))
      checks <- checks + 1L
      prev_ci <- c(NA_real_, NA_real_)
      if(u > 0 && u < n) prev_ci <- as.numeric(confint(svyciprop(reformulate(v[1]), d, method="logit", df=degf(d))))
      add_row(drug,age_group,ins_label,"prevalence_pct",n,u,100*coef(prev),100*SE(prev),100*prev_ci,degf(d))
      if(u == 0) {
        for(metric in c("annual_oop_usd","annual_total_usd","annual_records","oop_share_pct"))
          add_row(drug,age_group,ins_label,metric,n,u,0,0,c(NA,NA),0)
        next
      }
      for (j in 2:4) {
        fit <- svymean(reformulate(v[j]), du)
        manual <- manual_ratio(p[[v[j]]] * user_mask, as.numeric(user_mask))
        stopifnot(isTRUE(all.equal(as.numeric(coef(fit)), manual[[1]], tolerance=1e-8)),
                  isTRUE(all.equal(as.numeric(SE(fit)), manual[[2]], tolerance=1e-8)))
        checks <- checks + 1L
        add_row(drug,age_group,ins_label,c("annual_oop_usd","annual_total_usd","annual_records")[j-1],n,u,
                as.numeric(coef(fit)),as.numeric(SE(fit)),if(degf(du)>0) as.numeric(confint(fit,df=degf(du))) else c(NA,NA),degf(du))
      }
      ratio <- svyratio(reformulate(v[2]),reformulate(v[3]),du)
      manual <- manual_ratio(p[[v[2]]] * user_mask, p[[v[3]]] * user_mask)
      stopifnot(isTRUE(all.equal(as.numeric(coef(ratio)), manual[[1]], tolerance=1e-8)),
                isTRUE(all.equal(as.numeric(SE(ratio)), manual[[2]], tolerance=1e-8)))
      checks <- checks + 1L
      add_row(drug,age_group,ins_label,"oop_share_pct",n,u,100*coef(ratio),100*SE(ratio),if(degf(du)>0) 100*as.numeric(confint(ratio,df=degf(du))) else c(NA,NA),degf(du))
    }
  }
}
results <- do.call(rbind, rows)
write.csv(results, "results/estimates.csv", row.names=FALSE, na="")
write_json(list(
  full_design_strata=length(unique(p$VARSTR)), full_design_psus=nrow(psus),
  full_design_df=degf(design), adult_design_df=degf(adult),
  weighted_adult_population=sum(p$PERWT24F[p$AGELAST>=18]),
  manual_point_and_taylor_se_checks=checks, independent_checks="PASS",
  reportable_rows=sum(results$status=="reportable"), suppressed_rows=sum(results$status!="reportable"),
  ci_proportions="logit, domain design df", ci_means_ratios="t, user-domain design df",
  survey_version=as.character(packageVersion("survey")),
  R_version=paste(R.version$major,R.version$minor,sep=".")
), "results/design-audit.json", pretty=TRUE, auto_unbox=TRUE, digits=10)
# Avoid local path leakage while preserving package/runtime versions.
writeLines(trimws(capture.output(sessionInfo()), which="right"), "results/R-session.txt")

# Scientific figure, deliberately showing suppressed groups as missing estimates.
png("results/insurance-comparison.png", width=1800, height=850, res=160)
par(mfrow=c(1,2), mar=c(5.5,10.5,4.2,1), oma=c(3.5,0,2,0), family="sans", las=1)
for(metric in c("prevalence_pct","annual_oop_usd")) {
  z <- results[results$drug=="primary" & results$population=="All adults" &
               results$insurance!="All coverage" & results$metric==metric, ]
  yy <- 3:1
  maximum <- max(z$upper_95,na.rm=TRUE)*1.23
  plot(NA, xlim=c(0,maximum), ylim=c(.5,3.5), yaxt="n", ylab="",
       xlab=if(metric=="prevalence_pct") "Adults with observed use (%)" else "Annual self/family payments per user (USD)",
       main=if(metric=="prevalence_pct") "Observed use in 2024" else "Out-of-pocket spending", bty="n")
  axis(2,at=yy,labels=c("Any private*", "Public only", "Uninsured all year"),tick=FALSE)
  abline(v=axTicks(1),col="#e6e9ee",lwd=.7)
  ok <- z$status=="reportable"
  segments(z$lower_95[ok],yy[ok],z$upper_95[ok],yy[ok],col="#187e85",lwd=2)
  points(z$estimate[ok],yy[ok],pch=19,cex=1.3,col="#12555b")
  if(any(!ok)) text(rep(maximum*.03,sum(!ok)),yy[!ok],labels=paste0("Suppressed (users n=",z$unweighted_users[!ok],")"),adj=0,cex=.8,col="#707783")
}
mtext("GLP-1 receptor agonists and tirzepatide | US civilian noninstitutionalized adults",outer=TRUE,side=3,line=.2,cex=1.12,font=2)
mtext("MEPS 2024 HC-256 + HC-254A. Points and 95% survey-design CIs. Unadjusted descriptions; not causal effects.",outer=TRUE,side=1,line=.4,cex=.8)
mtext("*Includes TRICARE/CHAMPVA and mixed private/public coverage. Spending is conditional on observed use.",outer=TRUE,side=1,line=1.5,cex=.8)
invisible(dev.off())
cat("Survey analysis complete:",checks,"independent estimate/SE checks passed.\n")
print(results[results$drug=="primary" & results$population=="All adults" & results$metric %in% c("prevalence_pct","annual_oop_usd"),c("insurance","metric","unweighted_users","estimate","lower_95","upper_95","status")],row.names=FALSE)
