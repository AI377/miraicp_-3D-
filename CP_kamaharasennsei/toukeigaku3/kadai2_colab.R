library(dplyr)
library(tidyr)

# ─── 1-1. 母集団生成関数 ───────────────────────────────────────────
generate_population <- function(N = 100000, seed = NULL) {
  if (!is.null(seed)) set.seed(seed)
  x_pop <- rnorm(N, mean = 0, sd = 1)
  alpha <- -5; beta <- 22; delta <- 10
  eps0 <- rnorm(N, mean = 0, sd = 10)
  eps1 <- rnorm(N, mean = 0, sd = 10)
  y0_pop <- alpha + beta * x_pop + eps0
  y1_pop <- alpha + beta * x_pop + delta + eps1
  data.frame(id = seq_len(N), x = x_pop, y0 = y0_pop, y1 = y1_pop)
}

# ─── 1-2. 標本抽出＋観測値生成関数 ───────────────────────────────────
sample_from_population <- function(pop_df, n = 100, seed = NULL) {
  if (!is.null(seed)) set.seed(seed)
  idx <- sample(pop_df$id, size = n, replace = FALSE)
  samp <- pop_df[idx, ]
  logit_p1 <- -0.5 * samp$x
  p1 <- plogis(logit_p1)
  samp$z <- rbinom(n, size = 1, prob = p1)
  samp$y <- ifelse(samp$z == 1, samp$y1, samp$y0)
  samp[, c("id", "x", "y0", "y1", "z", "y")]
}

# ─── 任意の層数で層別推定する関数 ────────────────────────────────────
estimate_k_strata <- function(df, k) {
  df$stratum <- cut(df$x,
                    breaks = quantile(df$x, probs = seq(0, 1, length.out = k + 1)),
                    include.lowest = TRUE,
                    labels = paste0("s", seq_len(k)))

  strata_est <- df %>%
    group_by(stratum, z) %>%
    summarise(mean_y = mean(y), n = n(), .groups = "drop") %>%
    pivot_wider(names_from = z, values_from = c(mean_y, n)) %>%
    rename(mu0 = mean_y_0, mu1 = mean_y_1, n0 = n_0, n1 = n_1)

  broken <- any(is.na(strata_est$mu0) | is.na(strata_est$mu1))
  if (broken) {
    return(list(k = k, overall_effect = NA, broken = TRUE, strata = strata_est))
  }

  strata_est <- strata_est %>%
    mutate(n_total = n0 + n1, effect = mu1 - mu0)
  w <- strata_est$n_total / nrow(df)
  overall <- sum(strata_est$effect * w)
  list(k = k, overall_effect = overall, broken = FALSE, strata = strata_est)
}

# ─── 母集団・サンプル生成 ─────────────────────────────────────────
pop <- generate_population(N = 100000, seed = 42)
df  <- sample_from_population(pop, n = 100, seed = 42)
true_ate <- mean(pop$y1 - pop$y0)
cat(sprintf("真のATE: %.4f\n\n", true_ate))

# ─── 各層数で推定 ─────────────────────────────────────────────────
k_list  <- c(2, 3, 4, 5, 10, 20, 25)
results <- data.frame(k = integer(), estimate = numeric(),
                      bias = numeric(), broken = logical())

for (k in k_list) {
  res <- estimate_k_strata(df, k)
  if (res$broken) {
    cat(sprintf("層数 k=%2d : 破綻（空セルあり）\n", k))
    print(as.data.frame(res$strata))
    results <- rbind(results, data.frame(k=k, estimate=NA, bias=NA, broken=TRUE))
  } else {
    bias <- res$overall_effect - true_ate
    cat(sprintf("層数 k=%2d : 推定値 = %7.4f  バイアス = %+7.4f\n",
                k, res$overall_effect, bias))
    results <- rbind(results, data.frame(k=k, estimate=res$overall_effect,
                                         bias=bias, broken=FALSE))
  }
}

cat("\n=== 結果まとめ ===\n")
cat(sprintf("真のATE: %.4f\n", true_ate))
print(results)
