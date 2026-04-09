# Reactivate warm lapsed

## Snapshot

- Audience: Customers with decent path score but 60+ days of inactivity
- Customers: 7,879
- Value pool: EUR 1,490,732
- Owner: CRM
- KPI: 30-day reactivation rate
- Time window: Next 14 days
- Trigger: Winning path score between 50 and 80 and no purchase for 60+ days

## Why this matters

This is the cheapest pool to win back before customers become truly lost.

## Recommended move

Use a two-step win-back: editorial value first, offer second only if there is no click.

## Message and channel design

- Channel: Email + Push + Paid retargeting
- Offer strategy: Value-led reminder first, selective incentive only after no engagement
- Message angle: Rebuild the routine before the customer forgets it

## Deep dive questions

- Which customers are still warm enough for a low cost win back?
- What trigger should be tested before the customer slips into lost territory?
- Which editorial message can reopen the routine without blanket discounting?

## Sample to inspect

Companion sample file: `deepdives/samples/reactivate_warm_lapsed_sample.csv`

```csv
anonymized_card_code,total_revenue,total_discount,total_items,n_tickets,first_date,last_date,avg_basket,median_basket,max_basket,n_unique_categories,n_unique_brands,n_unique_channels,n_unique_markets,n_unique_cities,tenure_days,avg_inter_purchase_days,repeat_customer,discount_ratio,is_omnichannel,Axe_Desc_first_purchase,Market_Desc_first_purchase,brand_first_purchase,channel_recruitment,salesVatEUR_first_purchase,discountEUR_first_purchase,quantity_first_purchase,first_purchase_dt,countryIsoCode,age_category,age_generation,gender,customer_city,status,RFM_Segment_ID,loyalty_label,rfm_label,second_date,days_to_second,revenue_90d,revenue_365d,discount_365d,high_value,category_path,channel_path,brand_path,value_12m_proxy,margin_12m_proxy,first_purchase_discounted,customer_id,first_category_display,first_channel_display,first_brand_display,country_display,city_display,age_display,gender_display,value_band,days_since_last,risk_band,phase_proxy,winning_path_score,wp_tier,archetype,is_anomaly,high_value_anomaly
7.22912e+18,691.95,75.95,10,3,2025-06-14,2025-07-08,230.65,240.9,273.75,3,7,1,2,1,24,12.0,1,0.09890610756608932,0,FRAGRANCE|FRAGRANCE,SELECTIVE|SELECTIVE,JO MALONE|TOM FORD,store,273.75,56.25,2.0,2025-06-14 19:36:00,FR,,geny,2,XXXXXXX,3,8,Bronze,At Risk,2025-06-18,4.0,691.95,691.95,75.95,1,FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> Store,JO MALONE -> AVEDA -> KAYALI,691.95,616.0,1,7.22912e+18,Mixed Basket (Fragrance + 1 others),Store,Mixed Basket (Jo Malone + 1 others),FR,Xxxxxxx,Unknown,2,Premium,176,At Risk,Erosion,80.0,Elite,One-and-Done,1,1
-8.42927e+18,323.85,13.99,28,10,2025-02-18,2025-07-10,32.385000000000005,28.355,92.19,5,10,1,2,1,142,15.777777777777779,1,0.041410134975136154,0,MAEK UP,EXCLUSIVE,HUDA BEAUTY,store,22.0,0.0,1.0,2024-09-24 17:22:00,MC,,geny,2,,3,2,Bronze,Loyal,2025-02-18,0.0,195.67000000000002,323.85,13.99,0,SKINCARE -> SKINCARE -> SKINCARE -> SKINCARE -> SKINCARE,Store -> Store -> Store -> Store -> Store,MERCI HANDY -> BYOMA -> MERCI HANDY -> MERCI HANDY -> SUPERGOOP,323.85,309.86,0,-8.42927e+18,Make Up,Store,Huda Beauty,MC,Unknown,Unknown,2,Growth,174,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
2.84965e+18,200.3,0.0,6,3,2025-06-26,2025-07-12,66.76666666666667,70.9,99.5,2,4,1,2,1,16,8.0,1,0.0,0,MAKE UP|MAEK UP|MAKE UP,EXCLUSIVE|SELECTIVE|EXCLUSIVE,HUDA BEAUTY|LANCOME|HUDA BEAUTY,store,99.5,0.0,3.0,2025-06-26 11:56:00,FR,15-25yo,gena,2,SCHAARBEEK,2,5,Silver,Promising,2025-07-12,16.0,200.3,200.3,0.0,0,MAEK UP -> MAEK UP -> HAIRCARE,Store -> Store -> Store,HUDA BEAUTY -> RARE BEAUTY -> COLOR WOW,200.3,200.3,0,2.84965e+18,Mixed Basket (Make Up + 2 others),Store,Mixed Basket (Huda Beauty + 2 others),FR,Schaarbeek,15-25yo,2,Growth,172,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
-1.47386e+17,383.72,12.08,18,5,2025-05-22,2025-07-20,76.744,49.980000000000004,203.99,4,6,1,2,3,59,14.75,1,0.030520464881253158,0,MAEK UP|MAKE UP|SKINCARE|MAKE UP|MAEK UP|SKINCARE|SKINCARE|SKINCARE|MAKE UP|MAKE UP|SKINCARE|SKINCARE|MAKE UP|MAEK UP|MAEK UP|MAEK UP|MAKE UP|MAKE UP|SKINCARE|SKINCARE|SKINCARE|MAEK UP,EXCLUSIVE|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|EXCLUSIVE|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|EXCLUSIVE,BENEFIT|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|BENEFIT|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|HUDA BEAUTY,store,295.71,0.0,22.0,2023-02-20 14:02:00,FR,15-25yo,gena,2,,3,5,Bronze,Promising,2025-05-23,1.0,383.72,383.72,12.08,0,SKINCARE -> MAKE UP -> MAEK UP -> SKINCARE -> SKINCARE,Store -> Store -> Store -> Store -> Store,KIEHLS -> SEPHORA -> SEPHORA -> SEPHORA -> KIEHLS,383.72,371.64000000000004,0,-1.47386e+17,Mixed Basket (Make Up + 21 others),Store,Mixed Basket (Benefit + 21 others),FR,Unknown,15-25yo,2,Premium,164,At Risk,Erosion,80.0,Elite,One-and-Done,0,0
-6.72795e+18,308.81,30.990000000000002,6,4,2025-02-10,2025-07-22,77.2025,82.0,108.9,4,5,2,3,3,162,54.0,1,0.09120070629782225,1,,,,,,,,,FR,,,2,BOIS D ARCY,3,4,Bronze,Recent,2025-05-11,90.0,174.9,308.81,30.990000000000002,0,FRAGRANCE -> SKINCARE -> MAEK UP -> FRAGRANCE,estore -> estore -> Store -> Store,DIOR -> DRUNK ELEPHANT -> LANCOME -> GIVENCHY,308.81,277.82,0,-6.72795e+18,Fragrance,Estore,Dior,FR,Bois D Arcy,Unknown,2,Growth,162,At Risk,Erosion,80.0,Elite,Discount Explorers,0,0
4.48635e+18,189.0,0.0,6,3,2025-07-06,2025-07-23,63.0,61.0,90.5,2,3,1,1,1,17,8.5,1,0.0,0,,,,,,,,,FR,m60yo,babyboomers,2,LE CANNET,2,4,Silver,Recent,2025-07-13,7.0,189.0,189.0,0.0,0,MAEK UP -> MAEK UP -> MAEK UP,Store -> Store -> Store,RARE BEAUTY -> LANEIGE -> TOO FACED,189.0,189.0,0,4.48635e+18,Make Up,Store,Rare Beauty,FR,Le Cannet,m60yo,2,Growth,161,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
-4.96911e+18,494.91999999999996,68.66,21,10,2025-01-21,2025-07-30,49.492,47.099999999999994,128.6,4,18,2,3,3,190,21.11111111111111,1,0.12182831186344442,1,,,,,,,,,FR,26-35yo,genz,2,PARIS,4,1,No Loyalty,Champions,2025-01-22,1.0,325.21,494.91999999999996,68.66,1,MAKE UP -> HAIRCARE -> HAIRCARE -> HAIRCARE -> MAKE UP,Store -> Store -> Store -> estore -> Store,SEPHORA -> KERASTASE -> KERASTASE -> KERASTASE -> ANASTASIA,494.91999999999996,426.26,0,-4.96911e+18,Make Up,Store,Sephora,FR,Paris,26-35yo,2,Premium,154,At Risk,Erosion,80.0,Elite,Discount Explorers,0,0
-7.59653e+18,269.18,34.8,7,4,2025-04-04,2025-08-01,67.295,56.0,152.19,3,5,1,3,3,119,39.666666666666664,1,0.11448121586946508,0,MAEK UP,SELECTIVE,DIOR,store,47.0,0.0,1.0,2025-05-21 11:20:00,FR,15-25yo,gena,2,,2,4,Silver,Recent,2025-05-21,47.0,116.99000000000001,269.18,34.8,0,MAEK UP -> MAKE UP -> MAEK UP -> FRAGRANCE,Store -> Store -> Store -> Store,SEPHORA -> DIOR -> BENEFIT -> RABANNE,269.18,234.38,0,-7.59653e+18,Make Up,Store,Dior,FR,Unknown,15-25yo,2,Growth,152,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
3.61676e+18,446.13,-18.4,16,6,2025-03-01,2025-08-06,74.355,67.985,122.36999999999999,4,9,1,4,2,158,31.6,1,-0.043017791597503095,0,,,,,,,,,FR,46-60yo,,2,VIERZON,3,2,Bronze,Loyal,2025-04-04,34.0,279.35,446.13,-18.4,1,FRAGRANCE -> MAEK UP -> MAEK UP -> MAEK UP -> MAKE UP,Store -> Store -> Store -> Store -> Store,AZZARO -> DIOR -> SEPHORA -> FENTY -> HOURGLASS,446.13,464.53,0,3.61676e+18,Fragrance,Store,Azzaro,FR,Vierzon,46-60yo,2,Premium,147,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
6.58026e+18,278.5,47.5,3,3,2025-05-16,2025-08-11,92.83333333333333,86.25,136.0,1,3,1,1,2,87,43.5,1,0.14570552147239263,0,FRAGRANCE,SELECTIVE,ARMANI,store,56.25,18.75,1.0,2025-05-16 16:47:00,FR,15-25yo,gena,1,CHAUMONT,2,4,Silver,Recent,2025-05-23,7.0,278.5,278.5,47.5,0,FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> Store,ARMANI -> RABANNE -> GUCCI,278.5,231.0,1,6.58026e+18,Fragrance,Store,Armani,FR,Chaumont,15-25yo,1,Growth,142,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
-3.92089e+18,513.22,0.0,20,3,2025-07-26,2025-08-12,171.07333333333335,83.4,421.92,3,10,1,3,1,17,8.5,1,0.0,0,MAKE UP|MAEK UP|SKINCARE|SKINCARE|MAEK UP|MAEK UP|MAKE UP|MAEK UP|SKINCARE|MAEK UP|SKINCARE,SEPHORA|EXCLUSIVE|EXCLUSIVE|EXCLUSIVE|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA,SEPHORA|BEAUTYBLENDER|MERCI HANDY|MARIO BADESCU|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA|SEPHORA,store,121.92,2.0,11.0,2022-07-21 13:58:00,FR,15-25yo,gena,2,AMIENS,3,5,Bronze,Promising,2025-08-08,13.0,513.22,513.22,0.0,1,SKINCARE -> MAEK UP -> SKINCARE,Store -> Store -> Store,THE ORDINARY -> SEPHORA -> SUMMER FRIDAYS,513.22,513.22,1,-3.92089e+18,Mixed Basket (Make Up + 10 others),Store,Mixed Basket (Sephora + 10 others),FR,Amiens,15-25yo,2,Premium,141,At Risk,Erosion,80.0,Elite,One-and-Done,0,0
-8.7954e+18,316.17,42.230000000000004,5,3,2025-05-02,2025-08-21,105.39,137.67000000000002,154.0,2,3,1,2,2,111,55.5,1,0.11782924107142857,0,FRAGRANCE,SELECTIVE,DOLCE & GABBANA,store,117.0,0.0,1.0,2023-01-14 13:36:00,FR,,,2,CUGNAUX,2,4,Silver,Recent,2025-06-21,50.0,162.17000000000002,316.17,42.230000000000004,0,SKINCARE -> SKINCARE -> FRAGRANCE,Store -> Store -> Store,ERBORIAN -> RITUALS -> ARMANI,316.17,273.94,0,-8.7954e+18,Fragrance,Store,Dolce & Gabbana,FR,Cugnaux,Unknown,2,Growth,132,At Risk,Erosion,80.0,Elite,Rising Stars,0,0
```
