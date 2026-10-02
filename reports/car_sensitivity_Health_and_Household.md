# CAR sensitivity: Health_and_Household

Population: all priced items (loader.priced), n = 331,095. Top 20 by CAR under each (C, m).
C values: simple = 4.2486, count-weighted = 4.4768.

Scope: whole priced pool, because no candidate matcher exists until Step 7. Candidate-set-mean C sensitivity is deferred to Step 7 (DECISIONS.md #22).

## Top-20 overlap between every pair of settings

| | simple C, m=25 | simple C, m=50 | simple C, m=120 | simple C, m=500 | count-weighted C, m=25 | count-weighted C, m=50 | count-weighted C, m=120 | count-weighted C, m=500 |
|---|---|---|---|---|---|---|---|---|
| **simple C, m=25** | — | 10 | 5 | 5 | 15 | 16 | 5 | 5 |
| **simple C, m=50** | 10 | — | 15 | 15 | 5 | 14 | 15 | 15 |
| **simple C, m=120** | 5 | 15 | — | 20 | 0 | 9 | 20 | 20 |
| **simple C, m=500** | 5 | 15 | 20 | — | 0 | 9 | 20 | 20 |
| **count-weighted C, m=25** | 15 | 5 | 0 | 0 | — | 11 | 0 | 0 |
| **count-weighted C, m=50** | 16 | 14 | 9 | 9 | 11 | — | 9 | 9 |
| **count-weighted C, m=120** | 5 | 15 | 20 | 20 | 0 | 9 | — | 20 |
| **count-weighted C, m=500** | 5 | 15 | 20 | 20 | 0 | 9 | 20 | — |

## Compared with a raw average_rating sort

Median rating_number in the raw-sort top 20: 222.

| Setting | Overlap with raw-sort top 20 |
|---|---|
| simple C, m=25 | 15 / 20 |
| simple C, m=50 | 5 / 20 |
| simple C, m=120 | 0 / 20 |
| simple C, m=500 | 0 / 20 |
| count-weighted C, m=25 | 20 / 20 |
| count-weighted C, m=50 | 11 / 20 |
| count-weighted C, m=120 | 0 / 20 |
| count-weighted C, m=500 | 0 / 20 |

## Distinct values: CAR vs the star rating in the data (recorded to one decimal)

Distinct star ratings: 41. Distinct (rating, rating count) pairs: 35,520. CAR depends only on those two fields, so that is its upper bound. Values are compared at 1e-9 so float noise cannot add distinct values; the 2 dp column is what a two-decimal display would show.

| Setting | Distinct CAR | Distinct CAR at 2 dp |
|---|---|---|
| simple C, m=25 | 35,520 | 280 |
| simple C, m=50 | 35,520 | 256 |
| simple C, m=120 | 35,519 | 220 |
| simple C, m=500 | 35,519 | 187 |
| count-weighted C, m=25 | 35,519 | 274 |
| count-weighted C, m=50 | 35,520 | 253 |
| count-weighted C, m=120 | 35,520 | 221 |
| count-weighted C, m=500 | 35,520 | 181 |

## Rank of every item that reaches the top 20 under any setting

Blank = outside the top 20.

| parent_asin | title | rating | ratings | simple C, m=25 | simple C, m=50 | simple C, m=120 | simple C, m=500 | count-weighted C, m=25 | count-weighted C, m=50 | count-weighted C, m=120 | count-weighted C, m=500 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0C22HR3JS | Biotrue Hydration Plus Contact Lens Solution, Multi-Pur… | 4.9 | 42,315 | 16 | 5 | 1 | 1 |  | 11 | 1 | 1 |
| B0C81LJW31 | Electric Spin Scrubber, Up to 450RPM Cordless Cleaning … | 5.0 | 411 | 1 | 1 |  |  | 1 | 1 |  |  |
| B09TQ5C4KX | Tide PODS Laundry Detergent Soap PODS, High Efficiency … | 4.9 | 34,617 | 17 | 6 | 2 | 2 |  | 12 | 2 | 2 |
| B0C9FRCHCP | MEOLY Psoriasis Cream, Psoriasis Treatment, Eczema Crea… | 5.0 | 407 | 2 | 2 |  |  | 2 | 2 |  |  |
| B0BXW8PHBC | Dreft Blissfuls Laundry Scent Booster Beads for Washer,… | 4.9 | 29,984 | 18 | 7 | 3 | 3 |  | 13 | 3 | 3 |
| B0CB1R4XVX | Electric Spin Scrubber, Up to 450RPM Cordless Cleaning … | 5.0 | 406 | 3 | 3 |  |  | 3 | 3 |  |  |
| B0006SW71G | Advil Pain Reliever and Fever Reducer, Pain Relief Medi… | 4.9 | 16,978 | 19 | 8 | 4 | 4 |  | 15 | 4 | 4 |
| B0CFLPKXRT | Heating Pad for Back & Cramps Relief,Electric Heat Pad … | 5.0 | 375 | 4 | 4 |  |  | 4 | 4 |  |  |
| B000GCRZL4 | Clorox Disinfecting Wipes, Fresh Scent, 35-ct | 4.9 | 16,594 | 20 | 9 | 5 | 5 |  | 16 | 5 | 5 |
| B0C9F5KC52 | Blood Pressure Monitor, Blood Pressure Machine Automati… | 5.0 | 314 | 5 | 18 |  |  | 5 | 5 |  |  |
| B0BXB2VZT9 | Advil Liqui-Gels Pain Reliever and Fever Reducer, Pain … | 4.9 | 15,148 |  | 10 | 6 | 6 |  | 17 | 6 | 6 |
| B0CJBRXWGW | Smart Scale for Body Weight and Fat Percentage, RunSTAR… | 5.0 | 308 | 6 |  |  |  | 6 | 6 |  |  |
| B00MK2D954 | Tylenol Infants Oral Suspension Liquid Medicine with Ac… | 4.9 | 14,124 |  | 11 | 7 | 7 |  | 18 | 7 | 7 |
| B0CGWPD4P2 | Blood Pressure Monitors for Home Use,Extra Large Upper … | 5.0 | 279 | 7 |  |  |  | 7 | 7 |  |  |
| B000WZWZ1U | Aspirin Regimen Bayer 81mg Enteric Coated Tablets, #1 D… | 4.9 | 12,711 |  | 12 | 8 | 8 |  | 19 | 8 | 8 |
| B0C5R3KZXM | 8.6'' Thrusting Realistic Dildo Vibrator, Onismo Automa… | 5.0 | 266 | 8 |  |  |  | 8 | 8 |  |  |
| B07Z8HLQRV | Braun ThermoScan Lens Filters for Ear Thermometer, Disp… | 4.9 | 11,604 |  | 13 | 9 | 9 |  | 20 | 9 | 9 |
| B0C65NH99S | Acvioo Rose Realistic Dildo G-Spot Dildos with Strong S… | 5.0 | 228 | 9 |  |  |  | 9 | 9 |  |  |
| B0000UTUVA | Mrs. Meyer's Multi-Surface Cleaner Concentrate, Use to … | 4.9 | 11,309 |  | 14 | 10 | 10 |  |  | 10 | 10 |
| B0BWFN5HFK | Thrusting Vibrator Dildo G Spot Vibrators with Remote C… | 5.0 | 222 | 10 |  |  |  | 10 | 10 |  |  |
| B0C6B7MW2T | Advil - 300 Coated Tablets | 4.9 | 11,254 |  | 15 | 11 | 11 |  |  | 11 | 11 |
| B0C1RVL432 | Anal Plug Rose Vibrator Couples Sex Toys for Women, Amo… | 5.0 | 209 | 11 |  |  |  | 11 | 14 |  |  |
| B07DK33HTB | Little Remedies Infant Fever & Pain Reliever with Aceta… | 4.9 | 10,904 |  | 16 | 12 | 12 |  |  | 12 | 12 |
| B0C68W9MS6 | G Spot Vibrator for Woman, Clitoral Licking Thrusting D… | 5.0 | 186 | 12 |  |  |  | 12 |  |  |  |
| B000V5NVXW | Clorox Bleach Free Wipe, Crisp Lemon, 75 Count | 4.9 | 10,754 |  | 17 | 13 | 13 |  |  | 13 | 13 |
| B0C596N7S8 | Deep Neck Pain Relief w/Conductive Magnetic Therapy Hea… | 5.0 | 180 | 13 |  |  |  | 13 |  |  |  |
| B0C6NY1LX8 | simplehuman Code P Custom Fit Drawstring Trash Bags, 20… | 4.9 | 9,868 |  | 19 | 14 | 14 |  |  | 14 | 14 |
| B0BZ7G95RT | Adult Sex Toys Women Sex Toy - 3IN1 App Remote Control … | 5.0 | 179 | 14 |  |  |  | 14 |  |  |  |
| B073Q34KKQ | Tylenol Infants Liquid Pain Relief and Fever Medicine, … | 4.9 | 9,851 |  | 20 | 15 | 15 |  |  | 15 | 15 |
| B0CH821W7G | Anal Beads Rose Sex Toy,Vibrating Butt Plug with 9 Mode… | 5.0 | 174 | 15 |  |  |  | 15 |  |  |  |
| B0BSZG4PKT | Motrin Children's Oral Suspension 100mg Ibuprofen Medic… | 4.9 | 9,750 |  |  | 16 | 16 |  |  | 16 | 16 |
| B0CJ91HBF4 | Migraine Headache Relief Cap, Migraine Relief Cap Odorl… | 5.0 | 151 |  |  |  |  | 16 |  |  |  |
| B0C615HXJR | Motrin Children's Oral Suspension, Berry, 72 Count | 4.9 | 8,446 |  |  | 17 | 17 |  |  | 17 | 17 |
| B0CFPZXSS8 | Wrist Blood Pressure Monitor Adjustable Cuff Home Autom… | 5.0 | 145 |  |  |  |  | 17 |  |  |  |
| B09TQ693H8 | Tide PODS 4 in 1 Febreze Sport Odor Defense, Laundry De… | 4.9 | 8,109 |  |  | 18 | 18 |  |  | 18 | 18 |
| B0BWRQCJ47 | Thrusting Dildo G Spot Rabbit Vibrator - 3 in 1 Dildos … | 5.0 | 135 |  |  |  |  | 18 |  |  |  |
| B0BN572G61 | BlenderBottle Star Wars Shaker Bottle Pro Series Perfec… | 4.9 | 7,889 |  |  | 19 | 19 |  |  | 19 | 19 |
| B088VF81YB | CALBESTRAD FITS for Jeep Compass 2011 2012 2013 Tail Li… | 5.0 | 134 |  |  |  |  | 19 |  |  |  |
| B0BVH8L2Y4 | Excedrin Migraine Relief Caplets to Alleviate Migraine … | 4.9 | 7,594 |  |  | 20 | 20 |  |  | 20 | 20 |
| B0BL6RG2PR | Double Tongue Licking Kneading Rose Swing Toy, Skin Fri… | 5.0 | 133 |  |  |  |  | 20 |  |  |  |
