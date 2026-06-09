library(dplyr)
library(tidyr)

# ─── 元の関数を読み込み ───────────────────────────────────────────
source("toukeigaku3/R_code.R")

# ─── 任意の層数で層別推定する関数 ────────────────────────────────
estimate_k_strata <- function(df, k) {
  # k: 層の数
  # x を k 等分位数で k 層に分割
  df$stratum <- cut(df$x,
                    breaks = quantile(df$x, probs = seq(0, 1, length.out = k + 1)),
                    include.lowest = TRUE,
                    labels = paste0("s", seq_len(k)))

  # 各層ごとに z=0, z=1 の平均 y を計算
  strata_est <- df %>%
    group_by(stratum, z) %>%
    summarise(mean_y = mean(y), n = n(), .groups = "drop") %>%
    pivot_wider(names_from = z, values_from = c(mean_y, n),
                names_prefix = "") %>%
    rename(mu0 = `mean_y_0`, mu1 = `mean_y_1`,
           n0  = `n_0`,      n1  = `n_1`)

  # z=0 か z=1 が存在しない層があれば破綻（NA になる）
  broken <- any(is.na(strata_est$mu0) | is.na(strata_est$mu1))

  if (broken) {
    return(list(k = k, overall_effect = NA, broken = TRUE,
                strata = strata_est))
  }

  # 層ごとの重み（層のサンプルサイズ / 全体）
  strata_est <- strata_est %>%
    mutate(n_total = n0 + n1,
           effect  = mu1 - mu0)

  w <- strata_est$n_total / nrow(df)
  overall <- sum(strata_est$effect * w)

  list(k = k, overall_effect = overall, broken = FALSE,
       strata = strata_est)
}

# ─── 試す層の数 ───────────────────────────────────────────────────
k_list <- c(2, 3, 4, 5, 10, 20, 25)

# ─── 母集団・サンプル生成（シード固定で再現性を確保） ──────────────
set.seed(42)
pop <- generate_population(N = 100000, seed = 42)
df  <- sample_from_population(pop, n = 100, seed = 42)

true_ate <- mean(pop$y1 - pop$y0)
cat(sprintf("真のATE: %.4f\n\n", true_ate))

# ─── 各層数で推定 ─────────────────────────────────────────────────
results <- data.frame(k = integer(), estimate = numeric(),
                      bias = numeric(), broken = logical())

for (k in k_list) {
  res <- estimate_k_strata(df, k)

  if (res$broken) {
    cat(sprintf("層数 k=%2d : 破綻（空セルあり）\n", k))
    cat("  詳細:\n")
    print(as.data.frame(res$strata))
    results <- rbind(results,
                     data.frame(k = k, estimate = NA,
                                bias = NA, broken = TRUE))
  } else {
    bias <- res$overall_effect - true_ate
    cat(sprintf("層数 k=%2d : 推定値 = %7.4f  バイアス = %+7.4f\n",
                k, res$overall_effect, bias))
    results <- rbind(results,
                     data.frame(k = k,
                                estimate = res$overall_effect,
                                bias = bias, broken = FALSE))
  }
}

# ─── まとめ表 ─────────────────────────────────────────────────────
cat("\n=== 結果まとめ ===\n")
cat(sprintf("真のATE: %.4f\n", true_ate))
print(results)
