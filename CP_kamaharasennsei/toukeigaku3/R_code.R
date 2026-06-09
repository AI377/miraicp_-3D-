#─── 1-1. 母集団生成関数 ───────────────────────────────────────────
generate_population <- function(N = 100000, seed = NULL) {
  # N: 母集団サイズ
  # seed: 乱数シード（省略可）
  if (!is.null(seed)) set.seed(seed)

  # 共変量 x を標準正規分布から生成
  x_pop <- rnorm(N, mean = 0, sd = 1)

  # 潜在的結果 y0, y1 を生成
  # y0 = α + β * x + ε0
  # y1 = α + β * x + δ + ε1   （δ = 10）
  alpha <- -5; beta <- 22; delta <- 10
  eps0 <- rnorm(N, mean = 0, sd = 10)
  eps1 <- rnorm(N, mean = 0, sd = 10)
  y0_pop <- alpha + beta * x_pop + eps0
  y1_pop <- alpha + beta * x_pop + delta + eps1

  # 母集団データフレームを返す
  data.frame(
    id = seq_len(N),
    x  = x_pop,
    y0 = y0_pop,
    y1 = y1_pop
  )
}

#─── 1-2. 標本抽出＋観測値生成関数 ───────────────────────────────────
sample_from_population <- function(pop_df, n = 100, seed = NULL) {
  # pop_df: generate_population() が返す母集団データフレーム
  # n: サンプルサイズ
  # seed: 乱数シード（省略可）
  if (!is.null(seed)) set.seed(seed)

  # 母集団からランダムサンプリング
  idx <- sample(pop_df$id, size = n, replace = FALSE)
  samp <- pop_df[idx, ]

  # 割り付け z の生成（x が大きいほど z=0 になりやすいロジスティックモデル）
  logit_p1 <- -0.5 * samp$x   # x↑ → p(z=1)↓
  p1 <- plogis(logit_p1)
  samp$z <- rbinom(n, size = 1, prob = p1)

  # 観測 y の作成
  samp$y <- ifelse(samp$z == 1, samp$y1, samp$y0)

  # 必要な列だけを返す
  samp[, c("id", "x", "y0", "y1", "z", "y")]
}

#─── 2-0. 真の平均因果効果を返す（神様視点） ───────────────────────────────────
I_am_god <- function(pop_df) {
  # pop_df: generate_population() が返すデータフレーム
  #         pop_df$y0, pop_df$y1 が潜在的結果として揃っていることを想定
  #
  # 真の平均因果効果 (ATE) = E[y1 - y0]
  ate <- mean(pop_df$y1 - pop_df$y0)

  # オプションで，サンプル内の分散なども返す
  var_te <- var(pop_df$y1 - pop_df$y0)

  list(
    ATE         = ate,
    var_TE      = var_te,
    se_ATE      = sqrt(var_te / nrow(pop_df))  # 標本標準誤差
  )
}

#─── 2-1. 単純効果推定関数 ───────────────────────────────────
estimate_simple <- function(df) {
  # df: sample_from_population() が返すデータフレーム
  # グループごとに観測 y の平均を計算し，差を取る
  mu1 <- mean(df$y[df$z == 1])
  mu0 <- mean(df$y[df$z == 0])
  est  <- mu1 - mu0

  list(
    est = est,
    mu1 = mu1,
    mu0 = mu0,
    diff = est
  )
}

#─── 2-2. 2層に分けた層別解析関数 ───────────────────────────────────
estimate_two <- function(df) {
  # df: sample_from_population() が返すデータフレーム
  # 共変量 x の中央値で 2層に分割
  med_x <- median(df$x)
  df$stratum <- ifelse(df$x <= med_x, "low", "high")

  # 各層ごとに平均差を計算
  library(dplyr)
  strata_est <- df %>%
    group_by(stratum, z) %>%
    summarise(mean_y = mean(y), .groups = "drop") %>%
    tidyr::pivot_wider(names_from = z, values_from = mean_y, names_prefix = "z") %>%
    mutate(effect = z1 - z0)

  # 全体の層別平均効果（層の大きさで加重平均）
  w <- table(df$stratum) / nrow(df)
  overall_effect <- sum(strata_est$effect * w)

  list(
    strata = strata_est,
    weights = w,
    overall_effect = overall_effect
  )
}


# 1) 母集団を生成
pop <- generate_population(N = 100000)

# 2) サンプルを取り，観測データを得る
df  <- sample_from_population(pop, n = 100)

# 3) 推定関数に渡してみる
print("--------------------------------------")
print("2-0. I am god")
god_res <- I_am_god(pop)
print(god_res)

print("--------------------------------------")
print("2-1. estimate simple")
simple_res <- estimate_simple(df)
print(simple_res)

print("--------------------------------------")
print("2-2. estimate two")
two_res <- estimate_two(df)
print(two_res$strata); print(two_res$overall_effect)
