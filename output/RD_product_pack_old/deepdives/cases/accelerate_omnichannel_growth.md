# Accelerate omnichannel growth

## Snapshot

- Audience: Repeat customers in growth or high-value states who are still mono-channel
- Customers: 6,753
- Value pool: EUR 2,994,133
- Owner: CRM + Omnichannel
- KPI: Omnichannel adoption within 45 days
- Time window: Next 30 days
- Trigger: Second purchase done within 60 days but customer still uses one channel only

## Why this matters

Comparable omnichannel peers are worth about EUR 199 more per customer.

## Recommended move

Push store-to-app or app-to-store adoption in the 45 days after purchase two.

## Message and channel design

- Channel: App inbox + Website personalization + Store receipt / advisor
- Offer strategy: Convenience and exclusivity, not price cuts
- Message angle: Show why the second channel makes the routine easier

## Deep dive questions

- Which mono channel repeaters are closest to a second channel conversion?
- What is the observed value gap between mono channel and omnichannel peers?
- Which channel to channel move should be tested first?

## Sample to inspect

Companion sample file: `deepdives/samples/accelerate_omnichannel_growth_sample.csv`

```csv
anonymized_card_code,total_revenue,total_discount,total_items,n_tickets,first_date,last_date,avg_basket,median_basket,max_basket,n_unique_categories,n_unique_brands,n_unique_channels,n_unique_markets,n_unique_cities,tenure_days,avg_inter_purchase_days,repeat_customer,discount_ratio,is_omnichannel,Axe_Desc_first_purchase,Market_Desc_first_purchase,brand_first_purchase,channel_recruitment,salesVatEUR_first_purchase,discountEUR_first_purchase,quantity_first_purchase,first_purchase_dt,countryIsoCode,age_category,age_generation,gender,customer_city,status,RFM_Segment_ID,loyalty_label,rfm_label,second_date,days_to_second,revenue_90d,revenue_365d,discount_365d,high_value,category_path,channel_path,brand_path,value_12m_proxy,margin_12m_proxy,first_purchase_discounted,customer_id,first_category_display,first_channel_display,first_brand_display,country_display,city_display,age_display,gender_display,value_band,days_since_last,risk_band,phase_proxy,winning_path_score,wp_tier,archetype,is_anomaly,high_value_anomaly
1.67657e+18,10955.15,3110.37,104,17,2025-02-25,2025-12-16,644.4205882352941,366.54,2204.25,7,28,1,4,1,294,18.375,1,0.22113437683071793,0,,,,,,,,,FR,m60yo,babyboomers,2,PARIS,4,1,No Loyalty,Champions,2025-03-04,7.0,4801.6,10955.15,3110.37,1,HAIRCARE -> MAEK UP -> FRAGRANCE -> SKINCARE -> MAKE UP,Store -> Store -> Store -> Store -> Store,BENEFIT -> RARE BEAUTY -> CREME DE LA MER -> SISLEY -> NARS,10955.15,7844.78,0,1.67657e+18,Haircare,Store,Benefit,FR,Paris,m60yo,2,Premium,15,Active,Acceleration,77.5,Elite,Premium Loyalists,1,1
-8.7315e+18,10351.81,1257.83,254,52,2025-01-07,2025-12-23,199.07326923076923,124.15,946.8,6,49,1,3,4,350,6.862745098039215,1,0.10834358343583436,0,,,,,,,,,MC,46-60yo,,2,,4,1,No Loyalty,Champions,2025-01-07,0.0,2423.22,10351.81,1257.83,1,MAEK UP -> MAKE UP -> MAEK UP -> MAEK UP -> SKINCARE,Store -> Store -> Store -> Store -> Store,YVES ST LAURENT -> BY TERRY -> YVES ST LAURENT -> HUDA BEAUTY -> DIOR,10351.81,9093.98,0,-8.7315e+18,Make Up,Store,Yves St Laurent,MC,Unknown,46-60yo,2,Premium,8,Active,Acceleration,78.2,Elite,Premium Loyalists,1,1
-7.23321e+17,8683.58,3441.4,75,7,2025-04-21,2025-11-22,1240.5114285714285,1077.75,3695.24,4,7,1,2,1,215,35.833333333333336,1,0.2838272722924079,0,MAKE UP,SELECTIVE,LAUDER,store,236.6,101.4,2.0,2024-01-18 18:46:00,FR,,geny,1,00000,4,1,No Loyalty,Champions,2025-04-21,0.0,1172.95,8683.58,3441.4,1,FRAGRANCE -> FRAGRANCE -> FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> Store -> Store -> Store,CHANEL -> GIVENCHY -> DIOR -> CHANEL -> DIOR,8683.58,5242.18,1,-7.23321e+17,Make Up,Store,Lauder,FR,00000,Unknown,1,Premium,39,Cooling,Acceleration,75.0,Strong,Premium Loyalists,1,1
-5.82866e+18,7281.03,691.01,176,55,2025-02-28,2025-12-26,132.38236363636364,101.74,603.58,6,43,1,4,3,301,5.574074074074074,1,0.08667919378226903,0,SKINCARE|SKINCARE|SKINCARE,EXCLUSIVE|EXCLUSIVE|EXCLUSIVE,FENTY SKIN|THE ORDINARY|LANEIGE,store,65.9,0.0,3.0,2022-05-31 18:44:00,FR,26-35yo,genz,1,DAMMARIE LES LYS,4,1,No Loyalty,Champions,2025-03-05,5.0,5211.79,7281.03,691.01,1,MAEK UP -> MAEK UP -> FRAGRANCE -> HAIRCARE -> FRAGRANCE,Store -> Store -> Store -> Store -> Store,FENTY -> ANASTASIA -> HUGO BOSS -> GISOU -> DIOR,7281.03,6590.0199999999995,0,-5.82866e+18,Mixed Basket (Skincare + 2 others),Store,Mixed Basket (Fenty Skin + 2 others),FR,Dammarie Les Lys,26-35yo,1,Premium,5,Active,Acceleration,78.2,Elite,Premium Loyalists,1,1
-5.49496e+18,7228.56,1099.17,178,45,2025-02-18,2025-12-16,160.63466666666667,102.6,1083.15,7,46,1,4,3,301,6.840909090909091,1,0.1319891495041266,0,,,,,,,,,FR,15-25yo,gena,2,HENNEBONT,4,1,No Loyalty,Champions,2025-02-23,5.0,245.25,7228.56,1099.17,1,FRAGRANCE -> FRAGRANCE -> MAEK UP -> MAEK UP -> HAIRCARE,Store -> Store -> Store -> Store -> Store,KAYALI -> CHANEL -> SEPHORA -> SEPHORA -> SEPHORA,7228.56,6129.39,0,-5.49496e+18,Fragrance,Store,Kayali,FR,Hennebont,15-25yo,2,Premium,15,Active,Acceleration,78.5,Elite,Premium Loyalists,1,1
-3.48302e+18,6388.74,1120.74,159,73,2025-01-09,2025-12-24,87.51698630136985,63.89,305.9,7,57,1,4,4,349,4.847222222222222,1,0.14924335639751354,0,,,,,,,,,FR,46-60yo,,2,MANDELIEU LA NAPOULE,4,1,No Loyalty,Champions,2025-01-17,8.0,2050.18,6388.74,1120.74,1,FRAGRANCE -> MAEK UP -> MAEK UP -> MAEK UP -> FRAGRANCE,Store -> Store -> Store -> Store -> Store,KAYALI -> DIOR -> NARS -> CLARINS -> ARMANI,6388.74,5268.0,0,-3.48302e+18,Fragrance,Store,Kayali,FR,Mandelieu La Napoule,46-60yo,2,Premium,7,Active,Acceleration,78.2,Elite,Premium Loyalists,1,1
-5.46856e+18,6153.5599999999995,1172.8,205,83,2025-01-18,2025-12-22,74.13927710843373,62.97,577.8,7,44,1,4,5,338,4.121951219512195,1,0.16007949377316977,0,MAEK UP|MAEK UP,SEPHORA|SEPHORA,SEPHORA|SEPHORA,store,26.98,0.0,2.0,2024-03-20 17:37:00,FR,15-25yo,gena,2,PFASTATT,4,1,No Loyalty,Champions,2025-03-04,45.0,232.39,6153.5599999999995,1172.8,1,SKINCARE -> FRAGRANCE -> FRAGRANCE -> SKINCARE -> MAKE UP,Store -> Store -> Store -> Store -> Store,BYOMA -> LANCOME -> MUGLER THIERRY -> SOL DE JANEIRO -> SEPHORA,6153.5599999999995,4980.759999999999,0,-5.46856e+18,Mixed Basket (Make Up + 1 others),Store,Mixed Basket (Sephora + 1 others),FR,Pfastatt,15-25yo,2,Premium,9,Active,Acceleration,76.6,Elite,Premium Loyalists,1,1
-4.17605e+18,5904.860000000001,664.3100000000001,170,33,2025-01-15,2025-12-29,178.93515151515155,159.0,671.7,7,44,1,4,3,348,10.875,1,0.10112540853715157,0,,,,,,,,,FR,46-60yo,,2,LEVALLOIS PERRET,4,1,No Loyalty,Champions,2025-01-25,10.0,2420.8,5904.860000000001,664.3100000000001,1,MAKE UP -> HAIRCARE -> SKINCARE -> MAKE UP -> MAEK UP,Store -> Store -> Store -> Store -> Store,BENEFIT -> MAKEUP BY MARIO -> BYOMA -> SEPHORA -> MAKEUP BY MARIO,5904.860000000001,5240.55,0,-4.17605e+18,Make Up,Store,Benefit,FR,Levallois Perret,46-60yo,2,Premium,2,Active,Acceleration,78.6,Elite,Premium Loyalists,1,1
-8.32422e+18,5801.95,1361.81,96,30,2025-04-20,2025-12-14,193.39833333333334,54.0,2886.73,7,30,1,4,3,238,8.206896551724139,1,0.1900970998470077,0,,,,,,,,,FR,m60yo,babyboomers,2,LEVALLOIS PERRET,4,1,No Loyalty,Champions,2025-04-20,0.0,3657.4999999999995,5801.95,1361.81,1,OTHERS -> MAEK UP -> MAKE UP -> HAIRCARE -> MAKE UP,Store -> Store -> Store -> Store -> Store,BENEFIT SERVICE -> FENTY -> BENEFIT -> BENEFIT -> RARE BEAUTY,5801.95,4440.139999999999,0,-8.32422e+18,Others,Store,Benefit Service,FR,Levallois Perret,m60yo,2,Premium,17,Active,Acceleration,78.1,Elite,Premium Loyalists,1,1
-1.40063e+18,5771.84,682.92,168,17,2025-01-28,2025-12-23,339.52,44.91,2075.04,5,21,1,3,2,329,20.5625,1,0.1058009902769429,0,SKINCARE,SELECTIVE,DIOR,store,81.0,0.0,1.0,2022-10-17 15:03:00,MC,,,2,,4,1,No Loyalty,Champions,2025-03-27,58.0,5015.870000000001,5771.84,682.92,1,MAKE UP -> MAEK UP -> SKINCARE -> MAKE UP -> MAEK UP,Store -> Store -> Store -> Store -> Store,SEPHORA -> BENEFIT -> GISOU -> CHARLOTTE TILBURY -> CHARLOTTE TILBURY,5771.84,5088.92,0,-1.40063e+18,Skincare,Store,Dior,MC,Unknown,Unknown,2,Premium,8,Active,Acceleration,75.3,Elite,Premium Loyalists,1,1
3.07431e+18,5511.25,515.18,120,36,2025-01-21,2025-12-29,153.09027777777777,124.275,474.21,7,42,1,4,6,342,9.771428571428572,1,0.08548676413730848,0,,,,,,,,,FR,46-60yo,,2,PARIS,4,1,No Loyalty,Champions,2025-02-11,21.0,1501.37,5511.25,515.18,1,MAEK UP -> FRAGRANCE -> MAEK UP -> MAEK UP -> MAEK UP,Store -> Store -> Store -> Store -> Store,HAUS LABS -> MAISON FRANCIS KURKDJIAN -> ANASTASIA -> ARMANI -> BENEFIT,5511.25,4996.07,0,3.07431e+18,Make Up,Store,Haus Labs,FR,Paris,46-60yo,2,Premium,2,Active,Acceleration,78.3,Elite,Premium Loyalists,1,1
1.37639e+18,5368.41,873.11,138,34,2025-01-11,2025-12-30,157.89441176470586,120.75,819.4,7,35,1,4,1,353,10.696969696969697,1,0.13988739922326615,0,,,,,,,,,FR,,geny,2,CASTELNAU LE LEZ,4,1,No Loyalty,Champions,2025-01-25,14.0,1290.48,5368.41,873.11,1,MAEK UP -> MAEK UP -> FRAGRANCE -> SKINCARE -> HAIRCARE,Store -> Store -> Store -> Store -> Store,TOO FACED -> NARS -> YVES ST LAURENT -> RITUALS -> COLOR WOW,5368.41,4495.3,0,1.37639e+18,Make Up,Store,Too Faced,FR,Castelnau Le Lez,Unknown,2,Premium,1,Active,Acceleration,78.1,Elite,Premium Loyalists,1,1
```
