$ErrorActionPreference = "Stop"

$notebooks = @(
  "01_dataclean_1_da_prices.ipynb",
  "01_dataclean_2_load.ipynb",
  "01_dataclean_3_res_offshore.ipynb",
  "01_dataclean_4_res_onshore.ipynb",
  "01_dataclean_5_res_solar.ipynb",
  "01_dataclean_6_total_generation.ipynb",
  "01_dataclean_7_energy_prices.ipynb"
)

foreach ($nb in $notebooks) {
  Write-Host "Running $nb ..."
  jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 $nb
}

Write-Host "All 01_data_cleaning notebooks executed."
