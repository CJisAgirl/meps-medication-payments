suppressPackageStartupMessages(library(survey))
suppressPackageStartupMessages(library(jsonlite))
source("scripts/payment_helpers.R")
options(survey.lonely.psu="fail", survey.adjust.domain.lonely=FALSE)
p <- read.csv("data/processed/extension-persons.csv",colClasses=c(DUPERSID="character"))
p <- p[p$PERWT24F>0,]
stopifnot(!anyDuplicated(p$DUPERSID),all(is.finite(p$oop)),all(p$oop>=0))
p$payment_band <- payment_band(p$oop)
mask <- p$AGELAST>=18 & p$user==1
design <- svydesign(ids=~VARPSU,strata=~VARSTR,weights=~PERWT24F,nest=TRUE,data=p)
stopifnot(all(table(unique(p[c("VARSTR","VARPSU")])$VARSTR)>=2))
users <- design[mask,]; n <- sum(mask); df <- degf(users)
stopifnot(n==800L,all(p$oop[mask]<=p$total[mask]+.000001))
checks <- 0L; interval_checks <- 0L
manual <- function(x) {
  w <- p$PERWT24F; den <- sum(w*mask)
  e <- sum(w*x*mask)/den
  influence <- w*mask*(x-e)/den
  z <- aggregate(influence,p[c("VARSTR","VARPSU")],sum)
  se <- sqrt(sum(vapply(split(z$x,z$VARSTR),function(v) length(v)*var(v),numeric(1))))
  c(estimate=e,se=se)
}
verify <- function(x, fit) {
  m <- manual(x)
  stopifnot(isTRUE(all.equal(unname(m),c(as.numeric(coef(fit)),as.numeric(SE(fit))),tolerance=1e-8)))
  checks <<- checks+1L
  m
}
rows <- list()
add <- function(metric,kind,e,se,ci,status,count=NA_integer_,below=NA_integer_,above=NA_integer_,probability=NA_real_,se_method="Taylor") {
  visible <- !startsWith(status,"withheld:")
  scale <- if(kind=="proportion") 100 else 1
  rows[[length(rows)+1L]] <<- data.frame(metric,kind,denominator_users=n,
    sample_in_category=count,quantile_probability=probability,users_at_or_below=below,users_at_or_above=above,
    estimate=if(visible)e*scale else NA_real_,se=if(visible)se*scale else NA_real_,
    lower_95=if(visible)ci[1]*scale else NA_real_,upper_95=if(visible)ci[2]*scale else NA_real_,
    units=if(kind=="proportion")"percent of adult users" else "2024 USD per adult user",
    se_method,design_df=df,status)
}
fit <- svymean(~oop,users); m <- verify(p$oop,fit)
ci <- as.numeric(confint(fit,df=df))
stopifnot(isTRUE(all.equal(ci,unname(m[1]+c(-1,1)*qt(.975,df)*m[2]),tolerance=1e-8)))
interval_checks <- interval_checks+1L
add("mean_oop","mean",m[1],m[2],ci,payment_precision("mean",n,m[1],m[2],ci,df))
ids <- c("zero_oop_pct","oop_0_100_pct","oop_100_500_pct","oop_500_1000_pct","oop_over_1000_pct")
for(j in seq_along(levels(p$payment_band))) {
  indicator <- as.numeric(p$payment_band==levels(p$payment_band)[j])
  d <- update(users,indicator=indicator[mask])
  fit <- svymean(~indicator,d); m <- verify(indicator,fit)
  ci <- payment_beta_ci(m[1],m[2],n,df)
  if(all(is.finite(ci))) {
    package_ci <- as.numeric(confint(svyciprop(~indicator,d,method="beta",df=df)))
    stopifnot(isTRUE(all.equal(unname(ci),package_ci,tolerance=1e-8)))
    interval_checks <- interval_checks+1L
  }
  add(ids[j],"proportion",m[1],m[2],ci,payment_precision("proportion",n,m[1],m[2],ci,df),sum(indicator[mask]))
}
probs <- c(.5,.75,.9)
qs <- svyquantile(~oop,users,quantiles=probs,qrule="math",interval.type="beta",df=df)
for(j in seq_along(probs)) {
  v <- qs$oop[j,]; e <- unname(v[1]); ci <- unname(v[2:3]); se <- unname(v[4])
  independent <- weighted_inverse_cdf(p$oop[mask],p$PERWT24F[mask],probs[j])
  stopifnot(isTRUE(all.equal(e,independent,tolerance=1e-10)))
  indicator <- as.numeric(p$oop<=independent)
  fit <- svymean(indicator[mask],users); m <- verify(indicator,fit)
  probability_ci <- payment_beta_ci(m[1],m[2],n,df)
  independent_ci <- vapply(probability_ci,function(q) weighted_inverse_cdf(p$oop[mask],p$PERWT24F[mask],q),numeric(1))
  stopifnot(isTRUE(all.equal(ci,independent_ci,tolerance=1e-8)),
            isTRUE(all.equal(se,diff(independent_ci)/(2*qt(.975,df)),tolerance=1e-8)))
  interval_checks <- interval_checks+1L
  below <- sum(p$oop[mask]<=e); above <- sum(p$oop[mask]>=e)
  add(c("median_oop","p75_oop","p90_oop")[j],"quantile",e,se,ci,
      quantile_precision(n,below,above,e,ci,df),below=below,above=above,
      probability=probs[j],se_method="approximate: Woodruff CI width / (2*t)")
}
out <- do.call(rbind,rows)
base <- read.csv("results/estimates.csv")
base_mean <- subset(base,drug=="primary" & population=="All adults" & insurance=="All coverage" & metric=="annual_oop_usd")
stopifnot(isTRUE(all.equal(out$estimate[out$metric=="mean_oop"],base_mean$estimate,tolerance=1e-8)),
          isTRUE(all.equal(out$se[out$metric=="mean_oop"],base_mean$se,tolerance=1e-8)),
          sum(out$sample_in_category[out$kind=="proportion"])==n)
write.csv(out,"results/payment-distribution.csv",row.names=FALSE,na="")
write_json(list(status="PASS",plan="METHODS.md#payment-distribution",adult_users=n,
  zero_total_payment_users=sum(p$total[mask]==0),zero_oop_users=sum(p$oop[mask]==0),
  user_domain_df=df,independent_mean_proportion_point_se_checks=checks,
  independent_interval_checks=interval_checks,independent_quantile_point_checks=3,
  same_original_mean_and_se=TRUE,band_counts_partition_users=TRUE,
  quantile_method="inverse weighted CDF; beta Woodruff intervals",survey_version=as.character(packageVersion("survey")),
  reportable=sum(out$status=="reportable"),flagged=sum(startsWith(out$status,"flagged:")),withheld=sum(startsWith(out$status,"withheld:"))),
  "results/payment-distribution-audit.json",pretty=TRUE,auto_unbox=TRUE,digits=12)

png("results/selfpay-distribution.png",width=1600,height=1000,res=170)
par(mar=c(5,11,4,2),oma=c(3.5,0,0,0),las=1)
z <- out[out$kind=="proportion",]; yy <- 5:1
ok <- !startsWith(z$status,"withheld:")
upper <- max(c(z$upper_95[ok],1),na.rm=TRUE)*1.28
plot(NA,xlim=c(0,upper),ylim=c(.5,5.5),yaxt="n",ylab="",bty="n",
  xlab="Share of all observed adult users (%)",main="How annual self/family payments were distributed")
axis(2,at=yy,labels=paste0(c("$0","Over $0 to $100","Over $100 to $500","Over $500 to $1,000","Over $1,000"),
  " (n=",z$sample_in_category,")"),tick=FALSE,cex.axis=.88)
abline(v=axTicks(1),col="#e7ecef",lwd=.7)
segments(0,yy[ok],z$estimate[ok],yy[ok],col="#d5e7e6",lwd=15)
segments(z$lower_95[ok],yy[ok],z$upper_95[ok],yy[ok],col="#187e85",lwd=2)
points(z$estimate[ok],yy[ok],pch=19,col="#12555b",cex=1.1)
text(z$upper_95[ok]+upper*.025,yy[ok],sprintf("%.1f%%%s",z$estimate[ok],ifelse(startsWith(z$status[ok],"flagged:"),"*","")),adj=0,cex=.85)
if(any(!ok))text(rep(upper*.03,sum(!ok)),yy[!ok],"Withheld",adj=0,col="grey40")
mtext("MEPS 2024 | 800 users | Weighted percentages and 95% survey CIs; n is the unweighted count.",side=1,outer=TRUE,line=.25,cex=.72)
mtext("Recorded target-drug payments, including zeros. Dollar bands are not financial-hardship definitions.",side=1,outer=TRUE,line=1.2,cex=.72)
invisible(dev.off())
cat("Payment distribution:",checks,"point/SE checks;",interval_checks,"interval checks; 3 quantile point checks\n")
print(out[,c("metric","sample_in_category","estimate","lower_95","upper_95","status")],row.names=FALSE)
