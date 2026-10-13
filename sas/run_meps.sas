/* MEPS 2024 medication payments: DATA step, PROC SQL and PROC SURVEYMEANS.
   Upload person_source.csv and rx_source.csv from data/sas-inputs to SAS Studio.
   Set input_dir to that folder's path on the SAS server, then run the entire file.
   Published reference estimates come from the Python/SQL/R workflow.
   No patient-level data are published.
*/
%let input_dir=/home/your-user/meps-sas-inputs;
%let output_dir=%sysfunc(pathname(work));
%macro assert_no_errors;
  %if &syscc > 4 %then %do;
    %put ERROR: SAS reported an error; outputs must not be accepted.;
    %abort cancel;
  %end;
%mend;

%macro require_file(name);
  %if not %sysfunc(fileexist(&input_dir./&name.)) %then %do;
    %put ERROR: Required input &name. is missing. Set input_dir to the uploaded CSV folder.;
    %abort cancel;
  %end;
%mend;
%require_file(person_source.csv);
%require_file(rx_source.csv);

data persons;
  length DUPERSID $10;
  infile "&input_dir./person_source.csv" dsd dlm=',' firstobs=2 truncover lrecl=32767;
  input DUPERSID :$10. AGELAST INSCOV24 PERWT24F VARSTR VARPSU;
  if missing(DUPERSID) or nmiss(AGELAST,PERWT24F,VARSTR,VARPSU)>0 then do;
    put 'ERROR: Missing person key or design input.'; abort cancel;
  end;
  if PERWT24F>0 and (AGELAST<0 or VARSTR<=0 or VARPSU<=0) then do;
    put 'ERROR: Invalid age or survey design.'; abort cancel;
  end;
run;
data rx_raw;
  length DUPERSID $10 RXRECIDX $19 RXDRGNAM RXNAME $200;
  infile "&input_dir./rx_source.csv" dsd dlm=',' firstobs=2 truncover lrecl=32767;
  input DUPERSID :$10. RXRECIDX :$19. RXDRGNAM :$200. RXNAME :$200.
        PERWT24F RXXP24X RXSF24X RXPV24X RXMR24X RXMD24X RXTR24X
        RXVA24X RXOF24X RXSL24X RXWC24X RXOT24X;
  if missing(DUPERSID) or missing(RXRECIDX) or missing(PERWT24F) then do;
    put 'ERROR: Missing prescription key or weight.'; abort cancel;
  end;
run;

/* Duplicates cause a failure; they are never silently removed. */
proc sort data=persons nodupkey dupout=duplicate_persons; by DUPERSID; run;
proc sort data=rx_raw nodupkey dupout=duplicate_rx; by RXRECIDX; run;
proc sql noprint;
  select count(*) into :duplicates_p trimmed from duplicate_persons;
  select count(*) into :duplicates_r trimmed from duplicate_rx;
  select count(*) into :bad_link trimmed from rx_raw e left join persons p
    on e.DUPERSID=p.DUPERSID
    where missing(p.DUPERSID) or abs(e.PERWT24F-p.PERWT24F)>=.0001;
quit;
%macro check_keys;
  %if &duplicates_p ne 0 or &duplicates_r ne 0 or &bad_link ne 0 %then %do;
    %put ERROR: Duplicate IDs, unmatched prescriptions or inconsistent person weights.;
    %abort cancel;
  %end;
%mend;
%check_keys;

/* Exact brand map. Generic/brand conflicts require review, not fallback. */
proc format;
  value $brandmap
    'OZEMPIC','WEGOVY','RYBELSUS'='SEMAGLUTIDE'
    'MOUNJARO','ZEPBOUND','ZEPBOUND 2.5MG/0.5 ML','ZEPBOUND 2.5MG/0.5ML',
      'ZEPBOUND 5 MG/0.5 ML INJ','ZEPBOUND INJ'='TIRZEPATIDE'
    'TRULICITY','TRULICITY 0.75/0.5'='DULAGLUTIDE'
    'VICTOZA','SAXENDA'='LIRAGLUTIDE'
    'BYETTA','BYDUREON','BYDUREON BCISE'='EXENATIDE'
    'ADLYXIN'='LIXISENATIDE'
    'TANZEUM'='ALBIGLUTIDE'
    other='';
run;
data rx_clean;
  set rx_raw;
  length generic name $200 named ingredient $24 mapping_method $32;
  generic=strip(prxchange('s/\s+/ /',-1,upcase(RXDRGNAM)));
  name=strip(prxchange('s/\s+/ /',-1,upcase(RXNAME)));
  named=put(name,$brandmap.);
  exact_generic=generic in ('SEMAGLUTIDE','TIRZEPATIDE','DULAGLUTIDE',
    'LIRAGLUTIDE','EXENATIDE','LIXISENATIDE','ALBIGLUTIDE');
  generic_candidate=prxmatch('/SEMAGLUTIDE|TIRZEPATIDE|DULAGLUTIDE|LIRAGLUTIDE|EXENATIDE|LIXISENATIDE|ALBIGLUTIDE/',generic)>0;
  name_candidate=prxmatch('/SEMAGLUTIDE|TIRZEPATIDE|DULAGLUTIDE|LIRAGLUTIDE|EXENATIDE|LIXISENATIDE|ALBIGLUTIDE|OZEMPIC|WEGOVY|RYBELSUS|MOUNJARO|ZEPBOUND|TRULICITY|VICTOZA|SAXENDA|BYETTA|BYDUREON|ADLYXIN|TANZEUM/',name)>0;
  primary_flag=0; ingredient='other'; mapping_method='not_target';
  if (index(generic,'INSULIN')>0 and generic_candidate) or
     name in ('SOLIQUA','SOLIQUA 100/33','XULTOPHY','XULTOPHY 100/3.6') then do;
    ingredient='insulin_combination'; mapping_method='excluded_insulin_combination';
  end;
  else if exact_generic then do;
    if named ne '' and named ne generic then do;
      put 'ERROR: Conflicting generic and brand.'; abort cancel;
    end;
    ingredient=lowcase(generic); primary_flag=1; mapping_method='generic_exact';
  end;
  else if named ne '' then do;
    if generic not in ('','NAN','-1','-7','-8','-9','-15') then do;
      put 'ERROR: Brand fallback requires a missing generic.'; abort cancel;
    end;
    ingredient=lowcase(named); primary_flag=1; mapping_method='brand_fallback';
  end;
  else if generic_candidate or name_candidate then do;
    put 'ERROR: Unreviewed medication candidate.'; abort cancel;
  end;
  if primary_flag=1 then do;
    array dollars[11] RXXP24X RXSF24X RXPV24X RXMR24X RXMD24X RXTR24X
      RXVA24X RXOF24X RXSL24X RXWC24X RXOT24X;
    do k=1 to dim(dollars);
      if missing(dollars[k]) or dollars[k]<0 then do;
        put 'ERROR: Missing or negative target payment.'; abort cancel;
      end;
    end;
    residual=sum(RXSF24X,RXPV24X,RXMR24X,RXMD24X,RXTR24X,
      RXVA24X,RXOF24X,RXSL24X,RXWC24X,RXOT24X)-RXXP24X;
    if RXSF24X>RXXP24X+.02 or abs(residual)>.06000001 then do;
      put 'ERROR: Payment component reconciliation failed.'; abort cancel;
    end;
  end;
run;

/* Aggregate prescriptions BEFORE joining; retain zero payments and non-users. */
proc sql;
  create table rx_person as
  select DUPERSID, count(*) as fills, sum(RXSF24X) as oop, sum(RXXP24X) as total,
    sum(RXPV24X) as pay_private, sum(RXMR24X) as pay_medicare,
    sum(RXMD24X) as pay_medicaid, sum(RXTR24X) as pay_tricare,
    sum(RXVA24X+RXOF24X+RXSL24X+RXWC24X+RXOT24X) as pay_other
  from rx_clean where primary_flag=1 group by DUPERSID;
  create table cohort as
  select p.*, coalesce(r.fills,0) as fills, coalesce(r.oop,0) as oop,
    coalesce(r.total,0) as total, coalesce(r.pay_private,0) as pay_private,
    coalesce(r.pay_medicare,0) as pay_medicare,
    coalesce(r.pay_medicaid,0) as pay_medicaid,
    coalesce(r.pay_tricare,0) as pay_tricare, coalesce(r.pay_other,0) as pay_other
  from persons p left join rx_person r on p.DUPERSID=r.DUPERSID;
quit;
data analysis;
  set cohort;
  if PERWT24F>0;
  adult=(AGELAST>=18); target_user=(fills>0); adult_user=(adult and target_user);
  pay_self=oop;
  band_zero=(oop=0); band_0_100=(oop>0 and oop<=100);
  band_100_500=(oop>100 and oop<=500); band_500_1000=(oop>500 and oop<=1000);
  band_over_1000=(oop>1000);
run;
proc sql noprint;
  select count(*) into :n_person trimmed from persons;
  select count(*) into :n_rx trimmed from rx_raw;
  select count(*) into :n_cohort trimmed from cohort;
  select count(*), sum(adult), sum(adult_user), sum(fills*adult_user)
    into :n_positive trimmed, :n_adult trimmed, :n_users trimmed, :n_fills trimmed from analysis;
  create table strata_check as select VARSTR, count(distinct VARPSU) as psus
    from analysis group by VARSTR;
  select count(*) into :bad_strata trimmed from strata_check where psus<2;
quit;
%macro check_cohort;
  %if &n_person ne 19140 or &n_rx ne 204550 or &n_cohort ne &n_person or
      &n_positive ne 18683 or &n_adult ne 15126 or &n_users ne 800 or
      &n_fills ne 4368 or &bad_strata ne 0 %then %do;
    %put ERROR: Cohort or design differs from the pinned MEPS reference.;
    %abort cancel;
  %end;
%mend;
%check_cohort;

/* FULL design: never WHERE-filter to adult users before survey estimation. */
ods exclude all;
ods output Domain=adult_prevalence;
proc surveymeans data=analysis mean stderr clm varmethod=taylor;
  strata VARSTR; cluster VARPSU; weight PERWT24F;
  domain adult / dfadj;
  var target_user;
run;
ods output Domain=user_means;
proc surveymeans data=analysis mean stderr clm varmethod=taylor;
  strata VARSTR; cluster VARPSU; weight PERWT24F;
  domain adult_user / dfadj;
  var oop total fills band_zero band_0_100 band_100_500 band_500_1000 band_over_1000;
run;
ods output DomainRatio=payer_ratios;
proc surveymeans data=analysis ratio stderr clm df varmethod=taylor;
  strata VARSTR; cluster VARPSU; weight PERWT24F;
  domain adult_user / dfadj;
  ratio pay_self pay_private pay_medicare pay_medicaid pay_tricare pay_other / total;
run;
ods output DomainQuantiles=native_quantiles;
proc surveymeans data=analysis quantile=(.5 .75 .9) nonsymcl varmethod=taylor;
  strata VARSTR; cluster VARPSU; weight PERWT24F;
  domain adult_user / dfadj;
  var oop;
run;
ods exclude none;
%assert_no_errors;

/* Apply the existing payer-component support/precision gates before export.
   Contributor counts overlap across payers; users with zero payment stay in
   each ratio's denominator. Suppressed shares must never be rescaled. */
data payer_positive;
  set analysis;
  if adult_user=1;
  length Numerator $32;
  array payments[6] pay_self pay_private pay_medicare pay_medicaid pay_tricare pay_other;
  do j=1 to dim(payments);
    Numerator=upcase(vname(payments[j])); positive=(payments[j]>0); output;
  end;
  keep Numerator positive;
run;
proc sql;
  create table payer_support as select Numerator, sum(positive) as contributors
    from payer_positive group by Numerator;
  create table payer_joined as select r.*, p.contributors
    from payer_ratios r left join payer_support p
    on upcase(r.Numerator)=p.Numerator where r.adult_user=1;
quit;
data payer_report;
  set payer_joined;
  length status $48;
  status='reportable';
  if missing(contributors) then do;
    put 'ERROR: Payer output could not be matched to contributor counts.'; abort cancel;
  end;
  if &n_adult < 100 then status='withheld: adult n < 100';
  else if &n_users < 30 then status='withheld: user n < 30';
  else if contributors<30 then status='withheld: positive-payer users < 30';
  else if missing(DF) or DF<1 then status='withheld: design df < 1';
  else if nmiss(Ratio,StdErr)>0 or Ratio<=0 or StdErr<0 then
    status='withheld: invalid estimate or uncertainty';
  else if abs(StdErr/Ratio)>.30 then status='withheld: RSE > 30%';
  estimate_pct=Ratio*100; se_pct=StdErr*100;
  if status ne 'reportable' then call missing(estimate_pct,se_pct);
  /* CIs remain in local diagnostic ODS tables; their df convention differs. */
  keep Numerator Denominator contributors estimate_pct se_pct status;
run;
%assert_no_errors;

/* Comparable point estimates and Taylor SEs; CIs are deliberately not equated.
   R payment bands use beta CIs, whereas these SAS means use t-based CIs.
   Native SAS quantile conventions need separate review against R's inverse CDF. */
data sas_mean_checks;
  length metric $32;
  set user_means(where=(adult_user=1)) adult_prevalence(where=(adult=1));
  scale=100;
  select (upcase(VarName));
    when ('OOP') do; metric='mean_oop'; scale=1; end;
    when ('BAND_ZERO') metric='zero_oop_pct';
    when ('BAND_0_100') metric='oop_0_100_pct';
    when ('BAND_100_500') metric='oop_100_500_pct';
    when ('BAND_500_1000') metric='oop_500_1000_pct';
    when ('BAND_OVER_1000') metric='oop_over_1000_pct';
    when ('TARGET_USER') metric='prevalence_pct';
    otherwise delete;
  end;
  estimate=Mean*scale; se=StdErr*scale;
  keep metric estimate se;
run;

/* Separately reproduce R's inverse weighted empirical CDF definition. */
proc sort data=analysis(where=(adult_user=1)) out=ordered_users;
  by oop DUPERSID;
run;
proc sql;
  create table quantile_weight as select sum(PERWT24F) as total_weight from ordered_users;
quit;
data inverse_cdf_checks;
  length metric $32;
  if _n_=1 then set quantile_weight;
  set ordered_users;
  retain cumulative 0 next_quantile 1;
  array probabilities[3] _temporary_ (.5 .75 .9);
  array names[3] $32 _temporary_ ('median_oop' 'p75_oop' 'p90_oop');
  cumulative=cumulative+PERWT24F;
  do while (next_quantile<=3);
    if cumulative<probabilities[next_quantile]*total_weight then leave;
    metric=names[next_quantile]; estimate=oop; output;
    next_quantile=next_quantile+1;
  end;
  keep metric estimate;
run;

/* BEGIN R REFERENCES: generated from saved aggregate tables. */
data r_mean_reference;
length metric $32;
input metric $ estimate se;
datalines;
mean_oop 343.386487551339 28.8273309717611
zero_oop_pct 24.6179103858924 1.94441588395148
oop_0_100_pct 29.2806576523788 1.91283617207765
oop_100_500_pct 30.1587002617163 2.12035704469443
oop_500_1000_pct 6.92500565299348 1.01558270822062
oop_over_1000_pct 9.0177260470189 1.19875569206376
prevalence_pct 4.94251531059243 0.194200894437129
;
run;
data r_quantile_reference;
length metric $32;
input metric $ estimate;
datalines;
median_oop 88.03
p75_oop 299.94
p90_oop 963.7
;
run;
/* END R REFERENCES */

%macro compare_reference(actual, reference, variables);
  proc sort data=&actual.; by metric; run;
  proc sort data=&reference.; by metric; run;
  proc compare base=&reference. compare=&actual. method=absolute criterion=1e-6 briefsummary;
    id metric; var &variables.;
  run;
  %let compare_code=&sysinfo;
  %if &compare_code ne 0 %then %do;
    %put ERROR: Reference comparison failed for &actual. with SYSINFO=&compare_code.;
    %abort cancel;
  %end;
%mend;
%compare_reference(sas_mean_checks,r_mean_reference,estimate se);
%compare_reference(inverse_cdf_checks,r_quantile_reference,estimate);
%assert_no_errors;

title 'MEPS adult target-medication users: mean payments and payment bands';
proc print data=user_means(where=(adult_user=1)) noobs; run;
title 'MEPS adult prevalence';
proc print data=adult_prevalence(where=(adult=1)) noobs; run;
title 'Payment shares: ratios of weighted totals, not average individual shares';
proc print data=payer_report noobs; run;
title 'Native SAS survey quantiles: review definition and CI differences against R';
proc print data=native_quantiles(where=(adult_user=1)) noobs; run;
title 'Inverse weighted CDF point estimates aligned with the R definition';
proc print data=inverse_cdf_checks noobs; run;
title;

%macro export_result(data,name);
  proc export data=&data. outfile="&output_dir./&name..csv" dbms=csv replace; run;
%mend;
%export_result(sas_mean_checks,sas_mean_checks);
%export_result(inverse_cdf_checks,inverse_cdf_checks);
%export_result(user_means(where=(adult_user=1)),user_means);
%export_result(payer_report,payer_shares);
%export_result(native_quantiles(where=(adult_user=1)),native_quantiles);
%assert_no_errors;
%put NOTE: MEPS_SAS_REFERENCE_POINT_AND_SE_CHECKS_PASSED;
%put NOTE: Outputs are in &output_dir.;
%put NOTE: Save aggregate CSVs and the complete log before ending this SAS session.;
