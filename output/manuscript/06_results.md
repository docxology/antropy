# Computational results {#sec:results}

## Baseline outcomes

The baseline records 54 estimates: 45 finite,
3 undefined and 6 infinite. Its HDSE
values are displayed directly from the stored CSV.

| Shape | Field | $r$ | HDSE (nats) | Status |
|---|---|---|---|---|
| 64 | periodic | 0.2 | 0 | finite |
| 64 | periodic | 0.5 | 0.451985 | finite |
| 64 | periodic | 1 | 0.245482 | finite |
| 64 | noise | 0.2 | 1.4816 | finite |
| 64 | noise | 0.5 | 1.22536 | finite |
| 64 | noise | 1 | 0.680827 | finite |
| 64 | mixed | 0.2 | 2.70805 | finite |
| 64 | mixed | 0.5 | 1.02233 | finite |
| 64 | mixed | 1 | 0.488638 | finite |
| 16x16 | periodic | 0.2 | 0.262364 | finite |
| 16x16 | periodic | 0.5 | 1.07654 | finite |
| 16x16 | periodic | 1 | 0.765302 | finite |
| 16x16 | noise | 0.2 | - | undefined |
| 16x16 | noise | 0.5 | - | infinite |
| 16x16 | noise | 1 | 3.31381 | finite |
| 16x16 | mixed | 0.2 | - | infinite |
| 16x16 | mixed | 0.5 | 3.17109 | finite |
| 16x16 | mixed | 1 | 1.75318 | finite |
| 8x8x8 | periodic | 0.2 | - | infinite |
| 8x8x8 | periodic | 0.5 | 1.86322 | finite |
| 8x8x8 | periodic | 1 | 0.898039 | finite |
| 8x8x8 | noise | 0.2 | - | undefined |
| 8x8x8 | noise | 0.5 | - | infinite |
| 8x8x8 | noise | 1 | - | infinite |
| 8x8x8 | mixed | 0.2 | - | undefined |
| 8x8x8 | mixed | 0.5 | - | infinite |
| 8x8x8 | mixed | 1 | 4.71253 | finite |

![Baseline HDSE tolerance demonstration. Finite estimates are plotted; undefined and infinite estimates remain annotated and recorded in the table.](../../output/figures/hdse-tolerance.png){#fig:baseline width=100%}

## Replicated native HDSE

The replicated report contains 150 fields and 1650
estimates: 1528 finite, 105 undefined and
17 infinite. The tables retain the finite conditional mean and
sample SD, the finite fraction and the undefined/infinite counts (U/I). A dash
indicates an unavailable finite mean or SD; it does not denote zero entropy.

| Shape | $p$ | $r$ | Mean | SD | Finite/n | U/I |
|---|---|---|---|---|---|---|
| 6x7x8 | 0 | 1.5 | 0.620344 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | 2 | 0.334022 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | 2.5 | 0.181913 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | 1.5 | 3.71297 | 1.44226 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | 2 | 2.21524 | 0.731486 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | 2.5 | 1.18716 | 0.254853 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | 1.5 | 5.22817 | 0.343375 | 3/5 | 0/2 |
| 6x7x8 | 0.5 | 2 | 2.40793 | 0.402156 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | 2.5 | 1.14763 | 0.136496 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | 1.5 | 5.2898 | 0.184894 | 2/5 | 0/3 |
| 6x7x8 | 0.75 | 2 | 3.29457 | 0.316691 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | 2.5 | 1.44975 | 0.191395 | 5/5 | 0/0 |
| 6x7x8 | 1 | 1.5 | - | - | 0/5 | 0/5 |
| 6x7x8 | 1 | 2 | 4.14886 | 0.305753 | 5/5 | 0/0 |
| 6x7x8 | 1 | 2.5 | 1.68958 | 0.112868 | 5/5 | 0/0 |
| 10x12 | 0 | 1.5 | 0.195222 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | 2 | 0.0950618 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | 2.5 | 0.0471768 | 0 | 5/5 | 0/0 |
| 10x12 | 0.25 | 1.5 | 0.845984 | 0.198192 | 5/5 | 0/0 |
| 10x12 | 0.25 | 2 | 0.412154 | 0.0775165 | 5/5 | 0/0 |
| 10x12 | 0.25 | 2.5 | 0.204453 | 0.0403457 | 5/5 | 0/0 |
| 10x12 | 0.5 | 1.5 | 1.39016 | 0.187022 | 5/5 | 0/0 |
| 10x12 | 0.5 | 2 | 0.637592 | 0.0698127 | 5/5 | 0/0 |
| 10x12 | 0.5 | 2.5 | 0.301306 | 0.0347635 | 5/5 | 0/0 |
| 10x12 | 0.75 | 1.5 | 1.84024 | 0.161139 | 5/5 | 0/0 |
| 10x12 | 0.75 | 2 | 0.977935 | 0.0408192 | 5/5 | 0/0 |
| 10x12 | 0.75 | 2.5 | 0.434886 | 0.0426958 | 5/5 | 0/0 |
| 10x12 | 1 | 1.5 | 2.00003 | 0.179567 | 5/5 | 0/0 |
| 10x12 | 1 | 2 | 1.06436 | 0.127857 | 5/5 | 0/0 |
| 10x12 | 1 | 2.5 | 0.425303 | 0.0656491 | 5/5 | 0/0 |
| 48 | 0 | 1.5 | 0.163193 | 0 | 5/5 | 0/0 |
| 48 | 0 | 2 | 0.0943835 | 0 | 5/5 | 0/0 |
| 48 | 0 | 2.5 | 0.0497278 | 0 | 5/5 | 0/0 |
| 48 | 0.25 | 1.5 | 0.34872 | 0.0451071 | 5/5 | 0/0 |
| 48 | 0.25 | 2 | 0.190946 | 0.0265122 | 5/5 | 0/0 |
| 48 | 0.25 | 2.5 | 0.0761487 | 0.0129646 | 5/5 | 0/0 |
| 48 | 0.5 | 1.5 | 0.395644 | 0.0426951 | 5/5 | 0/0 |
| 48 | 0.5 | 2 | 0.189375 | 0.0111342 | 5/5 | 0/0 |
| 48 | 0.5 | 2.5 | 0.0752926 | 0.00613628 | 5/5 | 0/0 |
| 48 | 0.75 | 1.5 | 0.387622 | 0.0279628 | 5/5 | 0/0 |
| 48 | 0.75 | 2 | 0.196965 | 0.023594 | 5/5 | 0/0 |
| 48 | 0.75 | 2.5 | 0.0802966 | 0.00841765 | 5/5 | 0/0 |
| 48 | 1 | 1.5 | 0.415829 | 0.022104 | 5/5 | 0/0 |
| 48 | 1 | 2 | 0.237607 | 0.0212663 | 5/5 | 0/0 |
| 48 | 1 | 2.5 | 0.0810962 | 0.015752 | 5/5 | 0/0 |

![Native HDSE across Bernoulli replacement probabilities and configured radii. Finite conditional summaries are accompanied by outcome counts; variability is across generated fields, not template pairs.](../../output/study/figures/mix-entropy.png){#fig:mix width=100%}

![Finite, undefined and infinite outcomes across the replicated design. These statuses are retained rather than imputed as zero.](../../output/study/figures/degeneracy.png){#fig:degeneracy width=100%}

Matching probabilities provide another view of these outcomes. A positive base
count followed by zero extended matches gives infinite continuation entropy;
zero base matches give undefined entropy. Increasing native feature count and
changing spatial geometry can therefore affect interpretability even when all
input amplitudes are valid.

![Base and extended template matching probabilities from observed pair counts. Sparse extended matches explain finite-sample degeneracy without reinterpreting it as zero entropy.](../../output/study/figures/match-probability.png){#fig:matches width=100%}

## Structured controls and alternative representations

| Shape | Control | $r$ | Mean | SD | Finite/n | U/I |
|---|---|---|---|---|---|---|
| 6x7x8 | checkerboard | 1.5 | 0 | 0 | 5/5 | 0/0 |
| 6x7x8 | checkerboard | 2 | 0 | 0 | 5/5 | 0/0 |
| 6x7x8 | checkerboard | 2.5 | 0 | 0 | 5/5 | 0/0 |
| 6x7x8 | constant | 1.5 | - | - | 0/5 | 5/0 |
| 6x7x8 | constant | 2 | - | - | 0/5 | 5/0 |
| 6x7x8 | constant | 2.5 | - | - | 0/5 | 5/0 |
| 6x7x8 | correlated | 1.5 | 2.56749 | 0.840728 | 5/5 | 0/0 |
| 6x7x8 | correlated | 2 | 1.37786 | 0.385547 | 5/5 | 0/0 |
| 6x7x8 | correlated | 2.5 | 0.753716 | 0.232607 | 5/5 | 0/0 |
| 6x7x8 | gaussian | 1.5 | 5.65724 | 0.495324 | 3/5 | 0/2 |
| 6x7x8 | gaussian | 2 | 3.3292 | 0.351848 | 5/5 | 0/0 |
| 6x7x8 | gaussian | 2.5 | 1.56662 | 0.232115 | 5/5 | 0/0 |
| 6x7x8 | shuffled | 1.5 | - | - | 0/5 | 0/5 |
| 6x7x8 | shuffled | 2 | 3.35688 | 0.471817 | 5/5 | 0/0 |
| 6x7x8 | shuffled | 2.5 | 1.76955 | 0.302802 | 5/5 | 0/0 |
| 10x12 | checkerboard | 1.5 | 0 | 0 | 5/5 | 0/0 |
| 10x12 | checkerboard | 2 | 0 | 0 | 5/5 | 0/0 |
| 10x12 | checkerboard | 2.5 | 0 | 0 | 5/5 | 0/0 |
| 10x12 | constant | 1.5 | - | - | 0/5 | 5/0 |
| 10x12 | constant | 2 | - | - | 0/5 | 5/0 |
| 10x12 | constant | 2.5 | - | - | 0/5 | 5/0 |
| 10x12 | correlated | 1.5 | 0.662661 | 0.109864 | 5/5 | 0/0 |
| 10x12 | correlated | 2 | 0.367965 | 0.0601135 | 5/5 | 0/0 |
| 10x12 | correlated | 2.5 | 0.185265 | 0.0324345 | 5/5 | 0/0 |
| 10x12 | gaussian | 1.5 | 1.74544 | 0.233531 | 5/5 | 0/0 |
| 10x12 | gaussian | 2 | 0.861448 | 0.128388 | 5/5 | 0/0 |
| 10x12 | gaussian | 2.5 | 0.400276 | 0.0465602 | 5/5 | 0/0 |
| 10x12 | shuffled | 1.5 | 1.79204 | 0.0637443 | 5/5 | 0/0 |
| 10x12 | shuffled | 2 | 0.850403 | 0.0587828 | 5/5 | 0/0 |
| 10x12 | shuffled | 2.5 | 0.409024 | 0.027914 | 5/5 | 0/0 |
| 48 | checkerboard | 1.5 | 0 | 0 | 5/5 | 0/0 |
| 48 | checkerboard | 2 | 0 | 0 | 5/5 | 0/0 |
| 48 | checkerboard | 2.5 | 0 | 0 | 5/5 | 0/0 |
| 48 | constant | 1.5 | - | - | 0/5 | 5/0 |
| 48 | constant | 2 | - | - | 0/5 | 5/0 |
| 48 | constant | 2.5 | - | - | 0/5 | 5/0 |
| 48 | correlated | 1.5 | 0.139492 | 0.0537352 | 5/5 | 0/0 |
| 48 | correlated | 2 | 0.0738259 | 0.0204956 | 5/5 | 0/0 |
| 48 | correlated | 2.5 | 0.0390499 | 0.0114501 | 5/5 | 0/0 |
| 48 | gaussian | 1.5 | 0.354011 | 0.0389952 | 5/5 | 0/0 |
| 48 | gaussian | 2 | 0.172839 | 0.026053 | 5/5 | 0/0 |
| 48 | gaussian | 2.5 | 0.0831918 | 0.0118893 | 5/5 | 0/0 |
| 48 | shuffled | 1.5 | 0.360859 | 0.0357175 | 5/5 | 0/0 |
| 48 | shuffled | 2 | 0.208973 | 0.018994 | 5/5 | 0/0 |
| 48 | shuffled | 2.5 | 0.0736555 | 0.00547319 | 5/5 | 0/0 |

![Native spatial HDSE and row-major flattened sample entropy. Their template feature counts and extension geometries differ; the comparison does not isolate flattening alone.](../../output/study/figures/native-v-flattened.png){#fig:geometry width=100%}

The geometry comparison is read together with feature counts and populations.
Neither a difference nor an agreement alone establishes estimator superiority.
The observed tables are specific to the declared synthetic design, radius,
finite sample and block geometry.

## Related entropy and statistical complexity

The recorded normalization options make these related-measure summaries
dimensionless. Display labels are DistEn: distribution entropy; PermEn: permutation; Spectral: spectral; Shannon: shannon; C-JS: statistical complexity.

| Shape | $p$ | Estimator | Finite mean | SD | Finite/n | U/I |
|---|---|---|---|---|---|---|
| 6x7x8 | 0 | DistEn | 0.821272 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | PermEn | 0.401562 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | Spectral | 0.366254 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | Shannon | 0.655986 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0 | C-JS | 0.304078 | 0 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | DistEn | 0.895451 | 0.00818597 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | PermEn | 0.496046 | 0.00286137 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | Spectral | 0.817511 | 0.0262881 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | Shannon | 0.723031 | 0.00469153 | 5/5 | 0/0 |
| 6x7x8 | 0.25 | C-JS | 0.278564 | 0.00207836 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | DistEn | 0.851999 | 0.00667078 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | PermEn | 0.503431 | 0.000895235 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | Spectral | 0.908797 | 0.0156529 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | Shannon | 0.744093 | 0.00724335 | 5/5 | 0/0 |
| 6x7x8 | 0.5 | C-JS | 0.274515 | 0.00490519 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | DistEn | 0.829532 | 0.00809795 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | PermEn | 0.503852 | 0.000556784 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | Spectral | 0.923803 | 0.00685935 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | Shannon | 0.727915 | 0.00931895 | 5/5 | 0/0 |
| 6x7x8 | 0.75 | C-JS | 0.28245 | 0.00532371 | 5/5 | 0/0 |
| 6x7x8 | 1 | DistEn | 0.813712 | 0.00826181 | 5/5 | 0/0 |
| 6x7x8 | 1 | PermEn | 0.503478 | 0.000811645 | 5/5 | 0/0 |
| 6x7x8 | 1 | Spectral | 0.923819 | 0.00686466 | 5/5 | 0/0 |
| 6x7x8 | 1 | Shannon | 0.657322 | 0.00954592 | 5/5 | 0/0 |
| 6x7x8 | 1 | C-JS | 0.317542 | 0.00516416 | 5/5 | 0/0 |
| 10x12 | 0 | DistEn | 0.9211 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | PermEn | 0.630036 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | Spectral | 0.322933 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | Shannon | 0.702175 | 0 | 5/5 | 0/0 |
| 10x12 | 0 | C-JS | 0.288771 | 0 | 5/5 | 0/0 |
| 10x12 | 0.25 | DistEn | 0.919696 | 0.0121944 | 5/5 | 0/0 |
| 10x12 | 0.25 | PermEn | 0.918879 | 0.0172518 | 5/5 | 0/0 |
| 10x12 | 0.25 | Spectral | 0.659491 | 0.0456326 | 5/5 | 0/0 |
| 10x12 | 0.25 | Shannon | 0.712075 | 0.00929196 | 5/5 | 0/0 |
| 10x12 | 0.25 | C-JS | 0.288816 | 0.00161396 | 5/5 | 0/0 |
| 10x12 | 0.5 | DistEn | 0.895524 | 0.0103245 | 5/5 | 0/0 |
| 10x12 | 0.5 | PermEn | 0.943309 | 0.0145696 | 5/5 | 0/0 |
| 10x12 | 0.5 | Spectral | 0.827952 | 0.0306717 | 5/5 | 0/0 |
| 10x12 | 0.5 | Shannon | 0.704415 | 0.00672185 | 5/5 | 0/0 |
| 10x12 | 0.5 | C-JS | 0.293462 | 0.00222378 | 5/5 | 0/0 |
| 10x12 | 0.75 | DistEn | 0.884852 | 0.00745327 | 5/5 | 0/0 |
| 10x12 | 0.75 | PermEn | 0.96377 | 0.00709848 | 5/5 | 0/0 |
| 10x12 | 0.75 | Spectral | 0.902698 | 0.0121331 | 5/5 | 0/0 |
| 10x12 | 0.75 | Shannon | 0.683502 | 0.0056531 | 5/5 | 0/0 |
| 10x12 | 0.75 | C-JS | 0.302502 | 0.00211954 | 5/5 | 0/0 |
| 10x12 | 1 | DistEn | 0.895472 | 0.00992491 | 5/5 | 0/0 |
| 10x12 | 1 | PermEn | 0.965971 | 0.00735781 | 5/5 | 0/0 |
| 10x12 | 1 | Spectral | 0.91021 | 0.0134747 | 5/5 | 0/0 |
| 10x12 | 1 | Shannon | 0.66164 | 0.00852925 | 5/5 | 0/0 |
| 10x12 | 1 | C-JS | 0.31495 | 0.00483384 | 5/5 | 0/0 |
| 48 | 0 | DistEn | 0.909918 | 0 | 5/5 | 0/0 |
| 48 | 0 | PermEn | 0.999673 | 0 | 5/5 | 0/0 |
| 48 | 0 | Spectral | 0.179052 | 0 | 5/5 | 0/0 |
| 48 | 0 | Shannon | 0.5 | 0 | 5/5 | 0/0 |
| 48 | 0 | C-JS | 0.331184 | 0 | 5/5 | 0/0 |
| 48 | 0.25 | DistEn | 0.915257 | 0.00752288 | 5/5 | 0/0 |
| 48 | 0.25 | PermEn | 0.993391 | 0.0035118 | 5/5 | 0/0 |
| 48 | 0.25 | Spectral | 0.777561 | 0.0341609 | 5/5 | 0/0 |
| 48 | 0.25 | Shannon | 0.578943 | 0.0354646 | 5/5 | 0/0 |
| 48 | 0.25 | C-JS | 0.325202 | 0.00666305 | 5/5 | 0/0 |
| 48 | 0.5 | DistEn | 0.929259 | 0.00851251 | 5/5 | 0/0 |
| 48 | 0.5 | PermEn | 0.986552 | 0.00983542 | 5/5 | 0/0 |
| 48 | 0.5 | Spectral | 0.845927 | 0.0531868 | 5/5 | 0/0 |
| 48 | 0.5 | Shannon | 0.613281 | 0.0207336 | 5/5 | 0/0 |
| 48 | 0.5 | C-JS | 0.322901 | 0.00458086 | 5/5 | 0/0 |
| 48 | 0.75 | DistEn | 0.948009 | 0.0133912 | 5/5 | 0/0 |
| 48 | 0.75 | PermEn | 0.993387 | 0.00574809 | 5/5 | 0/0 |
| 48 | 0.75 | Spectral | 0.882617 | 0.0293371 | 5/5 | 0/0 |
| 48 | 0.75 | Shannon | 0.629339 | 0.0270578 | 5/5 | 0/0 |
| 48 | 0.75 | C-JS | 0.320595 | 0.00573027 | 5/5 | 0/0 |
| 48 | 1 | DistEn | 0.958792 | 0.00697917 | 5/5 | 0/0 |
| 48 | 1 | PermEn | 0.999151 | 0.00116918 | 5/5 | 0/0 |
| 48 | 1 | Spectral | 0.880134 | 0.0274742 | 5/5 | 0/0 |
| 48 | 1 | Shannon | 0.63448 | 0.0272821 | 5/5 | 0/0 |
| 48 | 1 | C-JS | 0.318596 | 0.00497193 | 5/5 | 0/0 |

![Normalized Shannon entropy and Jensen-Shannon statistical complexity of the complete configured fixed-bin amplitude alphabet. This is a descriptive distributional extension, not a causal ordinal classification.](../../output/study/figures/entropy-complexity.png){#fig:statistical width=100%}

The entropy-complexity plane separates distributional uncertainty from distance
to the uniform alphabet. A high normalized entropy and a high statistical
complexity are different conditions. These fixed-amplitude-bin observations
do not carry the causal ordinal interpretation of a Bandt-Pompe analysis.
