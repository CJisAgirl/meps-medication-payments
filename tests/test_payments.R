source("scripts/payment_helpers.R")
count <- 0L
check <- function(name, code) {
  force(code); count <<- count+1L; cat("PASS",name,"\n")
}
check("zero and exact boundary dollars partition once", {
  actual <- as.integer(payment_band(c(0,.01,100,100.01,500,500.01,1000,1000.01)))
  stopifnot(identical(actual,c(1L,2L,2L,3L,3L,4L,4L,5L)))
})
check("invalid dollars are not silently binned", {
  stopifnot(inherits(try(payment_band(c(0,-1)),silent=TRUE),"try-error"),
            inherits(try(payment_band(c(0,NA)),silent=TRUE),"try-error"))
})
check("zero payments remain in weighted median", {
  stopifnot(weighted_inverse_cdf(c(0,100,1000),c(6,3,1),.5)==0)
})
check("ties and exact CDF boundary use lower observed quantile", {
  stopifnot(weighted_inverse_cdf(c(20,0,10,10),c(1,1,1,1),.5)==10,
            weighted_inverse_cdf(c(0,100),c(1,1),.5)==0,
            weighted_inverse_cdf(c(-999,0,100),c(0,1,1),1)==100)
})
check("invalid weights fail", {
  stopifnot(inherits(try(weighted_inverse_cdf(1:2,c(0,0),.5),silent=TRUE),"try-error"),
            inherits(try(weighted_inverse_cdf(1:2,c(1,-1),.5),silent=TRUE),"try-error"))
})
check("mean and rare proportion use different precision rules", {
  stopifnot(payment_precision("mean",100,.02,.012,c(.001,.05),100)=="withheld: RSE > 50%",
            payment_precision("proportion",100,.02,.012,c(.001,.05),100)=="flagged: rare, low precision",
            payment_precision("proportion",59,.3,.02,c(.2,.4),100)=="withheld: denominator n < 60",
            payment_precision("mean",100,100,30,c(40,160),100)=="flagged: low precision")
})
check("quantile zero is not rejected by an RSE divided by zero", {
  stopifnot(quantile_precision(100,60,100,0,c(0,10),99)=="reportable",
            quantile_precision(100,29,71,10,c(0,20),99)=="withheld: quantile support")
})
check("degenerate proportions require review", {
  stopifnot(grepl("requires review",payment_precision("proportion",100,0,0,c(0,0),99)),
            all(is.na(payment_beta_ci(0,0,100,99))))
})
cat("Payment helper tests:",count,"passed\n")
