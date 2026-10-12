# Follow-up estimands and reporting gates are in METHODS.md.
suppressPackageStartupMessages(library(survey))
suppressPackageStartupMessages(library(jsonlite))
options(survey.lonely.psu="fail", survey.adjust.domain.lonely=FALSE)
p <- read.csv("data/processed/extension-persons.csv", colClasses=c(DUPERSID="character"))
p <- p[p$PERWT24F > 0, ]
p$age_band <- cut(p$AGELAST, c(18,35,50,65,75,Inf), right=FALSE,
                  labels=c("18-34","35-49","50-64","65-74","75+"))
design <- svydesign(ids=~VARPSU,strata=~VARSTR,weights=~PERWT24F,nest=TRUE,data=p)
stopifnot(all(table(unique(p[c("VARSTR","VARPSU")])$VARSTR)>=2))
adult <- p$AGELAST >= 18
ages <- levels(p$age_band)
ins_labels <- c("All coverage","Any private incl. TRICARE","Public only","Uninsured all year")
history_labels <- c(all_12="Covered in every month",some_months="Some fully uninsured months",none_12="Uninsured in all 12 months")
source_labels <- c(stable_sources="Same source mix each month",changed_sources="Source mix changed")
payer_labels <- c(pay_self="Self/family",pay_private="Private insurance",pay_medicare="Medicare",pay_medicaid="Medicaid",pay_tricare="TRICARE",pay_other="Other sources")
rows <- list(); checks <- 0L

# Full-design covariance of per-person linearized contributions, including zeros
# outside a domain. Independent of survey estimation routines.
psu_cov <- function(z) {
  z <- as.matrix(z)
  totals <- aggregate(z, p[c("VARSTR","VARPSU")], sum)
  parts <- split(totals[, -(1:2), drop=FALSE], totals$VARSTR)
  Reduce(`+`, lapply(parts, function(x) nrow(x)*cov(as.matrix(x))))
}
manual_ratio <- function(num, den) {
  w <- p$PERWT24F; e <- sum(w*num)/sum(w*den)
  influence <- w*(num-e*den)/sum(w*den)
  c(estimate=e,se=sqrt(as.numeric(psu_cov(influence))))
}
gate <- function(n,u,contributors,e,se,df) {
  if(n<100) return("suppressed: adult n < 100")
  if(u<30) return("suppressed: user n < 30")
  if(!is.na(contributors) && contributors<30) return("suppressed: positive-payer users < 30")
  if(df<1) return("suppressed: design df < 1")
  if(!is.finite(e) || e==0 || !is.finite(se) || abs(se/e)>.30) return("suppressed: RSE > 30%")
  "reportable"
}
add <- function(analysis, age, group, metric, mask, kind="mean", variable="oop", payer=FALSE) {
  mask <- mask & adult; mask[is.na(mask)] <- FALSE
  n <- sum(mask); u <- sum(mask & p$user==1)
  domain <- if(kind=="prevalence") mask else mask & p$user==1
  contributors <- if(payer) sum(domain & p[[variable]]>0) else NA_integer_
  d <- design[domain, ]; df <- if(any(domain)) degf(d) else 0
  e <- se <- NA_real_; ci <- c(NA_real_,NA_real_)
  if(any(domain)) {
    f <- if(kind=="ratio") svyratio(reformulate(variable),~total,d) else svymean(reformulate(if(kind=="prevalence") "user" else variable),d)
    e <- as.numeric(coef(f)); se <- as.numeric(SE(f))
    num <- if(kind=="prevalence") p$user*mask else p[[variable]]*domain
    den <- if(kind=="ratio") p$total*domain else as.numeric(domain)
    manual <- manual_ratio(num,den)
    stopifnot(isTRUE(all.equal(e,manual[[1]],tolerance=1e-8)),isTRUE(all.equal(se,manual[[2]],tolerance=1e-8)))
    checks <<- checks+1L
    if(df>0) {
      if(kind=="prevalence") {
        if(e>0 && e<1) ci <- as.numeric(confint(svyciprop(~user,d,method="logit",df=df)))
      } else ci <- as.numeric(confint(f,df=df))
    }
  }
  status <- gate(n,u,contributors,e,se,df)
  scale <- if(kind %in% c("prevalence","ratio")) 100 else 1
  rows[[length(rows)+1L]] <<- data.frame(analysis,age,group,metric,unweighted_adults=n,unweighted_users=u,
    positive_payer_users=contributors,estimate=if(status=="reportable") scale*e else NA_real_,
    se=if(status=="reportable") scale*se else NA_real_,lower_95=if(status=="reportable") scale*ci[1] else NA_real_,
    upper_95=if(status=="reportable") scale*ci[2] else NA_real_,rse=if(status=="reportable") abs(se/e) else NA_real_,design_df=df,status)
}
pair <- function(analysis,age,group,mask) {
  add(analysis,age,group,"prevalence_pct",mask,"prevalence")
  add(analysis,age,group,"annual_oop_usd",mask)
}
for(age in ages) for(ins in 0:3) pair("detailed_age",age,ins_labels[ins+1],p$age_band==age & (ins==0 | p$INSCOV24==ins))
for(h in names(history_labels)) pair("monthly_history","All adults",history_labels[[h]],p$monthly_history==h)
for(h in names(source_labels)) pair("source_changes","All adults",source_labels[[h]],p$source_history==h)
for(age in c("All adults",ages)) for(v in names(payer_labels)) {
  mask <- if(age=="All adults") adult else p$age_band==age
  add("payment_sources",age,payer_labels[[v]],"annual_payment_usd",mask,variable=v,payer=TRUE)
  add("payment_sources",age,payer_labels[[v]],"payment_share_pct",mask,"ratio",v,TRUE)
}
out <- do.call(rbind,rows)
stopifnot(!anyDuplicated(out[c("analysis","age","group","metric")]))
hidden <- out$status!="reportable"
stopifnot(all(is.na(as.matrix(out[hidden,c("estimate","se","lower_95","upper_95","rse")]))))
ok <- !hidden
stopifnot(all(is.finite(as.matrix(out[ok,c("estimate","se","lower_95","upper_95")]))),
          all(out$lower_95[ok]<=out$estimate[ok]),all(out$estimate[ok]<=out$upper_95[ok]))
write.csv(out,"results/extension-estimates.csv",row.names=FALSE,na="")

# Age-only standardized use among any-private/public-only adults.
mask <- adult & p$INSCOV24 %in% 1:2
p$cover_model <- factor(ifelse(p$INSCOV24==1,"Any private incl. TRICARE",ifelse(p$INSCOV24==2,"Public only",NA)),levels=ins_labels[2:3])
knots <- as.numeric(quantile(p$AGELAST[mask],c(1/3,2/3)))
basis <- splines::ns(p$AGELAST,knots=knots,Boundary.knots=c(18,85))
p$b1 <- basis[,1];p$b2 <- basis[,2];p$b3 <- basis[,3]
design_model <- svydesign(ids=~VARPSU,strata=~VARSTR,weights=~PERWT24F,nest=TRUE,data=p)
di <- design_model[mask, ]; lev <- levels(p$cover_model)
support <- do.call(rbind,lapply(ages,function(a) do.call(rbind,lapply(lev,function(g) {
  ix <- mask & !is.na(p$age_band) & !is.na(p$cover_model) & p$age_band==a & p$cover_model==g
  data.frame(age=a,group=g,adults=sum(ix),users=sum(p$user[ix]),nonusers=sum(1-p$user[ix]))
}))))
write.csv(support,"results/age-adjustment-support.csv",row.names=FALSE)
supported <- all(support$adults>=100 & support$users>=5 & support$nonusers>=5)
model_audit <- list(status="not estimated: insufficient support",support_gate=supported)
adjusted <- data.frame(group=c(lev,"Public only minus any private"),
  metric=c("age_adjusted_use_pct","age_adjusted_use_pct","age_adjusted_difference_pp"),
  estimate=NA_real_,se=NA_real_,lower_95=NA_real_,upper_95=NA_real_,design_df=0,
  status="suppressed: insufficient model support")
if(supported) {
  # Tight numerical convergence makes the final-score reconstruction agree with
  # the IRLS working-weight covariance; this does not alter the model formula.
  control <- glm.control(epsilon=1e-14,maxit=100)
  adjustment <- svyglm(user~b1+b2+b3,design=di,family=quasibinomial(),control=control)
  fit <- svyglm(user~b1+b2+b3+cover_model,design=di,family=quasibinomial(),control=control)
  stopifnot(fit$converged,fit$rank==length(coef(fit)),all(is.finite(vcov(fit))),fit$df.residual>0)
  margins <- svypredmeans(adjustment,~cover_model,predictat=factor(lev,levels=lev))
  # Recreate point predictions and both covariance components from raw model scores.
  mf <- di$variables; w <- weights(di); W <- sum(w)
  X <- model.matrix(fit); mu <- as.numeric(fitted(fit)); y <- mf$user
  bread <- crossprod(X,X*as.numeric(w*mu*(1-mu)))
  score <- X*as.numeric(w*(y-mu))
  beta_if <- score %*% solve(bread)
  fits <- matrix(0,nrow(mf),2); gradients <- matrix(0,ncol(X),2)
  for(j in 1:2) {
    new <- mf;new$cover_model <- factor(lev[j],levels=lev)
    M <- model.matrix(delete.response(terms(fit)),new)
    fits[,j] <- plogis(as.numeric(M %*% coef(fit)))
    gradients[,j] <- colSums(M*as.numeric(w*fits[,j]*(1-fits[,j])))/W
  }
  points <- colSums(fits*w)/W
  model_if <- matrix(0,nrow(p),2); dist_if <- model_if
  model_if[mask,] <- beta_if %*% gradients
  dist_if[mask,] <- sweep(fits,2,points)*as.numeric(w/W)
  manual_cov <- psu_cov(model_if)+psu_cov(dist_if)
  stopifnot(isTRUE(all.equal(unname(coef(margins)),unname(points),tolerance=1e-8)),
            isTRUE(all.equal(unname(as.matrix(vcov(margins))),unname(manual_cov),check.attributes=FALSE,tolerance=1e-7)))
  # An intercept-only adjustment must reproduce crude group means and survey SEs.
  null_model <- svyglm(user~1,design=di,family=quasibinomial(),control=control)
  null_margins <- svypredmeans(null_model,~cover_model,predictat=factor(lev,levels=lev))
  crude <- svyby(~user,~cover_model,di,svymean,covmat=TRUE,keep.var=TRUE)
  stopifnot(isTRUE(all.equal(unname(coef(null_margins)),unname(coef(crude)),tolerance=1e-7)),
            isTRUE(all.equal(unname(vcov(null_margins)),unname(vcov(crude)),check.attributes=FALSE,tolerance=1e-7)))
  model_rows <- list(); dfs <- fit$df.residual; critical <- qt(.975,dfs)
  for(j in 1:2) {
    pr <- points[j];se <- sqrt(manual_cov[j,j]); ix <- mask & !is.na(p$cover_model) & p$cover_model==lev[j]
    state <- gate(sum(ix),sum(p$user[ix]),NA,pr,se,dfs)
    ci <- plogis(qlogis(pr)+c(-1,1)*critical*se/(pr*(1-pr)))
    model_rows[[j]] <- data.frame(group=lev[j],metric="age_adjusted_use_pct",estimate=100*pr,se=100*se,lower_95=100*ci[1],upper_95=100*ci[2],design_df=dfs,status=state)
  }
  # A signed contrast is governed by support/finite-variance gates, not RSE.
  difference <- points[2]-points[1];contrast <- c(-1,1)
  difference_se <- sqrt(as.numeric(t(contrast)%*%manual_cov%*%contrast))
  model_rows[[3]] <- data.frame(group="Public only minus any private",metric="age_adjusted_difference_pp",estimate=100*difference,se=100*difference_se,lower_95=100*(difference-critical*difference_se),upper_95=100*(difference+critical*difference_se),design_df=dfs,status=if(all(vapply(model_rows,function(z) z$status=="reportable",logical(1)))) "reportable" else "suppressed: margin gate")
  adjusted <- do.call(rbind,model_rows)
  adjusted[adjusted$status!="reportable",c("estimate","se","lower_95","upper_95")] <- NA_real_
  model_audit <- list(status="estimated: age-adjusted association only",support_gate=TRUE,formula="user ~ natural spline(age, df=3) + annual coverage",spline_knots=knots,boundary_knots=c(18,85),reference_adults=sum(mask),reference_users=sum(p$user[mask]),converged=fit$converged,rank=fit$rank,df=dfs,point_reconstruction="PASS",two_component_covariance_reconstruction="PASS",intercept_only_crude_check="PASS",predictive_margins_method="survey::svypredmeans; model plus target-distribution variance components",adjusted_spending="not estimated; requires separate plan")
}
write.csv(adjusted,"results/age-adjusted-use.csv",row.names=FALSE,na="")
write_json(list(extension_rows=nrow(out),reportable=sum(ok),suppressed=sum(hidden),independent_mean_ratio_checks=checks,reporting_gate="PASS",age_adjustment=model_audit),"results/extension-design-audit.json",pretty=TRUE,auto_unbox=TRUE,digits=10)

# Scientific plots: no interpolation or bars for withheld estimates.
forest <- function(z,labels,title,xlab,reference=z) {
  yy <- rev(seq_len(nrow(z))); available <- z$status=="reportable"
  ref_ok <- reference$status=="reportable"
  upper <- max(c(reference$upper_95[ref_ok],1),na.rm=TRUE)*1.15
  lower <- min(c(reference$lower_95[ref_ok],0),na.rm=TRUE)
  plot(NA,xlim=c(lower,upper),ylim=c(.5,nrow(z)+.5),yaxt="n",ylab="",xlab=xlab,main=title,bty="n",las=1)
  axis(2,at=yy,labels=labels,las=1,cex.axis=.82)
  abline(v=axTicks(1),col="#e7ecef",lwd=.6)
  segments(z$lower_95[available],yy[available],z$upper_95[available],yy[available],col="#187e85",lwd=2)
  points(z$estimate[available],yy[available],pch=19,col="#12555b",cex=1.1)
  if(any(!available)) text(rep(upper*.03,sum(!available)),yy[!available],"Withheld",adj=0,col="#767676",cex=.8)
}
png("results/detailed-age.png",width=1900,height=1450,res=170)
par(mfrow=c(2,2),mar=c(4,9,3,1),oma=c(3,0,2,0))
for(ins in ins_labels[2:3]) for(metric in c("prevalence_pct","annual_oop_usd")) {
 z <- out[out$analysis=="detailed_age" & out$group==ins & out$metric==metric,]
 reference <- out[out$analysis=="detailed_age" & out$group %in% ins_labels[2:3] & out$metric==metric,]
 forest(z,paste0(z$age," (users ",z$unweighted_users,")"),paste(if(ins==ins_labels[2]) "Any private*" else "Public only",if(metric=="prevalence_pct") "| Use" else "| Self/family payments"),if(metric=="prevalence_pct") "Adults with recorded use (%)" else "Annual USD per user",reference)
}
mtext("Finer age groups retain precision gates",outer=TRUE,side=3,line=.4,font=2)
mtext("MEPS 2024 | Points and 95% survey CIs | *Includes TRICARE and mixed private/public coverage.",outer=TRUE,side=1,line=.5,cex=.85)
mtext("Withheld means insufficient sample size or precision; it is not zero.",outer=TRUE,side=1,line=1.6,cex=.85)
invisible(dev.off())
png("results/monthly-insurance.png",width=1900,height=1350,res=170)
par(mfrow=c(2,2),mar=c(4,12,3,1),oma=c(3,0,2,0))
for(analysis in c("monthly_history","source_changes")) for(metric in c("prevalence_pct","annual_oop_usd")) {
 z <- out[out$analysis==analysis & out$metric==metric,]
 labels <- if(analysis=="monthly_history") c("Covered in every month","Some uninsured months","All months uninsured") else c("Same source mix","Source mix changed")
 reference <- out[out$analysis %in% c("monthly_history","source_changes") & out$metric==metric,]
 forest(z,labels,paste(if(analysis=="monthly_history") "12-month history" else "All months covered",if(metric=="prevalence_pct") "| Use" else "| OOP"),if(metric=="prevalence_pct") "Adults with recorded use (%)" else "Annual USD per user",reference)
}
mtext("Monthly insurance histories and annual outcomes",outer=TRUE,side=3,line=.4,font=2)
mtext("Monthly coverage is not uninterrupted daily coverage. Incomplete histories are audited separately.",outer=TRUE,side=1,line=.5,cex=.85)
mtext("Source mix changes do not identify a plan switch within the same source. No purchase-month linkage.",outer=TRUE,side=1,line=1.6,cex=.85)
invisible(dev.off())
png("results/payment-sources.png",width=1900,height=1000,res=170)
par(mfrow=c(1,2),mar=c(4,10,3,1),oma=c(3,0,2,0))
for(metric in c("annual_payment_usd","payment_share_pct")) {
 z <- out[out$analysis=="payment_sources" & out$age=="All adults" & out$metric==metric,]
 forest(z,z$group,if(metric=="annual_payment_usd") "Annual payments per user" else "Share of all target payments",if(metric=="annual_payment_usd") "2024 USD" else "Ratio of weighted payment totals (%)")
}
mtext("Who paid for the observed target medicines?",outer=TRUE,side=3,line=.4,font=2)
mtext("MEPS edited/imputed payment sources; includes zero source payments among users. 95% survey CIs.",outer=TRUE,side=1,line=.5,cex=.85)
mtext("A zero payment does not establish denied coverage. Sparse payer components are withheld.",outer=TRUE,side=1,line=1.6,cex=.85)
invisible(dev.off())
cat("Extension complete:",checks,"independent mean/ratio checks;",model_audit$status,"\n")
