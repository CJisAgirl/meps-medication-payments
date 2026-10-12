# Estimand-specific rules for the all-user payment follow-up; see METHODS.md.
payment_band <- function(x) {
  if(any(!is.finite(x) | x < 0)) stop("Payments must be finite and nonnegative")
  cut(x, c(-Inf,0,100,500,1000,Inf), right=TRUE,
      labels=c("Zero", "Over 0 to 100", "Over 100 to 500", "Over 500 to 1000", "Over 1000"))
}

weighted_inverse_cdf <- function(x, w, probability) {
  if(length(x)!=length(w) || !length(x) || any(!is.finite(x)) ||
     any(!is.finite(w) | w<0) || sum(w)<=0 ||
     length(probability)!=1 || !is.finite(probability) || probability<0 || probability>1)
    stop("Invalid weighted quantile inputs")
  keep <- w>0; x <- x[keep]; w <- w[keep]
  ix <- order(x); x <- x[ix]; w <- w[ix]
  x[which(cumsum(w) >= probability*sum(w))[1]]
}

payment_precision <- function(kind, n, estimate, se, ci, df) {
  if(n<60) return("withheld: denominator n < 60")
  if(df<1 || any(!is.finite(c(estimate,se,ci))) || se<0 ||
     ci[1]>estimate || ci[2]<estimate) return("withheld: invalid uncertainty")
  if(estimate<=0 || se==0 || (kind=="proportion" && estimate>=1))
    return("withheld: boundary estimate requires review")
  rse <- se/estimate
  if(rse<.30) return("reportable")
  if(rse<=.50) return("flagged: low precision")
  if(kind=="proportion" && ci[2]<=.10) return("flagged: rare, low precision")
  "withheld: RSE > 50%"
}

quantile_precision <- function(n, below, above, estimate, ci, df) {
  if(n<60 || below<30 || above<30) return("withheld: quantile support")
  if(df<1 || any(!is.finite(c(estimate,ci))) || estimate<0 ||
     ci[1]<0 || ci[1]>estimate || ci[2]<estimate)
    return("withheld: invalid quantile interval")
  "reportable"
}

# Independent Korn-Graubard beta limits used for proportions and Woodruff inversion.
payment_beta_ci <- function(estimate, se, n, df) {
  if(estimate<=0 || estimate>=1 || se<=0 || n<2 || df<1) return(c(NA_real_,NA_real_))
  effective <- estimate*(1-estimate)/se^2 * (qt(.025,n-1)/qt(.025,df))^2
  c(qbeta(.025,effective*estimate,effective*(1-estimate)+1),
    qbeta(.975,effective*estimate+1,effective*(1-estimate)))
}
