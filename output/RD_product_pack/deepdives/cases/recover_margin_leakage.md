# Recover margin leakage

## Snapshot

- Audience: Repeat customers with upside still intact but discount reliance above 30%
- Customers: 504
- Value pool: EUR 49,221
- Owner: CRM + Merchandising
- KPI: Margin per active customer
- Time window: Next 30 days
- Trigger: Discount ratio above 30% with repeat behavior still present

## Why this matters

Low-promo peers generate about EUR 167 more margin per customer.

## Recommended move

Replace blanket discounts with bundles, loyalty benefits, and replenishment-led offers.

## Message and channel design

- Channel: CRM + Merchandising
- Offer strategy: Bundles, gifts, replenishment cues, exclusives
- Message angle: Move the habit from price to routine and exclusivity

## Deep dive questions

- Where is discount intensity above thirty percent while retention remains salvageable?
- Which bundles or exclusives can replace blanket discounting?
- What KPI will prove margin recovery without suppressing repeat rate?

## Sample to inspect

Companion sample file: `deepdives/samples/recover_margin_leakage_sample.csv`

```csv
anonymized_card_code,total_revenue,total_discount,total_items,n_tickets,first_date,last_date,avg_basket,median_basket,max_basket,n_unique_categories,n_unique_brands,n_unique_channels,n_unique_markets,n_unique_cities,tenure_days,avg_inter_purchase_days,repeat_customer,discount_ratio,is_omnichannel,Axe_Desc_first_purchase,Market_Desc_first_purchase,brand_first_purchase,channel_recruitment,salesVatEUR_first_purchase,discountEUR_first_purchase,quantity_first_purchase,first_purchase_dt,countryIsoCode,age_category,age_generation,gender,customer_city,status,RFM_Segment_ID,loyalty_label,rfm_label,second_date,days_to_second,revenue_90d,revenue_365d,discount_365d,high_value,category_path,channel_path,brand_path,value_12m_proxy,margin_12m_proxy,first_purchase_discounted,customer_id,first_category_display,first_channel_display,first_brand_display,country_display,city_display,age_display,gender_display,value_band,days_since_last,risk_band,phase_proxy,winning_path_score,wp_tier,archetype,is_anomaly,high_value_anomaly
7.28471e+18,1732.4499999999998,756.5500000000001,25,6,2025-11-27,2025-11-28,288.7416666666666,203.35,634.75,4,7,1,2,1,1,0.2,1,0.30395741261550824,0,OTHERS|MAEK UP|FRAGRANCE|MAEK UP|FRAGRANCE|MAEK UP,OTHERS|SELECTIVE|SELECTIVE|SELECTIVE|SELECTIVE|SELECTIVE,SEPHORA SERVICE|DIOR|CHANEL|DIOR|CHANEL|DIOR,store,520.9,227.1,9.0,2025-11-27 15:52:00,FR,26-35yo,genz,2,VITRY SUR SEINE,4,8,No Loyalty,At Risk,2025-11-28,1.0,1732.4499999999998,1732.4499999999998,756.5500000000001,1,FRAGRANCE -> FRAGRANCE -> FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> Store -> Store -> Store,DIOR -> SEPHORA SERVICE -> CHANEL -> CHANEL -> CHANEL,1732.4499999999998,975.8999999999997,1,7.28471e+18,Mixed Basket (Others + 5 others),Store,Mixed Basket (Sephora Service + 5 others),FR,Vitry Sur Seine,26-35yo,2,Premium,33,Cooling,Promo Dependence,74.6,Strong,Discount Explorers,1,1
-2.57866e+18,1636.47,840.46,71,29,2025-01-08,2025-12-11,56.43,53.309999999999995,109.61999999999999,6,20,2,3,8,337,12.035714285714286,1,0.3393152006717993,1,MAKE UP|SKINCARE|MAEK UP,EXCLUSIVE|EXCLUSIVE|EXCLUSIVE,MILK MAKEUP|FIRST AID BEAUTY|CHARLOTTE TILBURY,estore,89.0,0.0,3.0,2022-06-05 13:40:00,FR,15-25yo,gena,2,LE PEAGE DE ROUSSILLON,4,1,No Loyalty,Champions,2025-01-18,10.0,769.37,1636.47,840.46,1,SKINCARE -> MAEK UP -> MAEK UP -> MAEK UP -> MAEK UP,estore -> Store -> estore -> estore -> estore,CLINIQUE -> CHARLOTTE TILBURY -> HUDA BEAUTY -> BENEFIT -> HAUS LABS,1636.47,796.01,0,-2.57866e+18,Mixed Basket (Make Up + 2 others),Estore,Mixed Basket (Milk Makeup + 2 others),FR,Le Peage De Roussillon,15-25yo,2,Premium,20,Active,Promo Dependence,80.4,Elite,Premium Loyalists,1,1
-1.42202e+18,1587.31,852.44,26,16,2025-01-15,2025-12-08,99.206875,58.835,419.69,5,15,2,3,3,327,21.8,1,0.34939645455477,1,,,,,,,,,FR,m60yo,babyboomers,2,BOULOGNE BILLANCOURT,4,1,No Loyalty,Champions,2025-01-27,12.0,865.3199999999999,1587.31,852.44,1,SKINCARE -> FRAGRANCE -> MAEK UP -> SKINCARE -> FRAGRANCE,estore -> estore -> Store -> Store -> Store,SISLEY -> CLINIQUE -> SEPHORA -> NEURAE -> CHANEL,1587.31,734.8699999999999,0,-1.42202e+18,Skincare,Estore,Sisley,FR,Boulogne Billancourt,m60yo,2,Premium,23,Active,Promo Dependence,79.4,Elite,Premium Loyalists,1,1
-2.16911e+18,1283.61,566.92,42,15,2025-01-08,2025-12-26,85.574,53.53,329.7,4,14,2,4,2,352,25.142857142857142,1,0.3063554765391537,1,,,,,,,,,FR,26-35yo,genz,2,LYON,4,1,No Loyalty,Champions,2025-01-08,0.0,292.7,1283.61,566.92,1,SKINCARE -> SKINCARE -> SKINCARE -> FRAGRANCE -> SKINCARE,estore -> Store -> Store -> estore -> Store,THE ORDINARY -> SEPHORA -> OLE HENRIKSEN -> MUGLER THIERRY -> SEPHORA,1283.61,716.6899999999999,0,-2.16911e+18,Skincare,Estore,The Ordinary,FR,Lyon,26-35yo,2,Premium,5,Active,Promo Dependence,79.5,Elite,Premium Loyalists,1,1
-8.00069e+18,1429.32,729.63,29,16,2025-01-11,2025-11-30,89.3325,77.58,200.9,4,12,2,3,4,323,21.533333333333335,1,0.33795595080942126,1,,,,,,,,,FR,46-60yo,,2,NICE,4,1,No Loyalty,Champions,2025-01-27,16.0,196.96,1429.32,729.63,1,FRAGRANCE -> MAEK UP -> FRAGRANCE -> MAEK UP -> FRAGRANCE,estore -> estore -> Store -> Store -> Store,DIOR -> SEPHORA -> DIOR -> SEPHORA -> DIOR,1429.32,699.6899999999999,0,-8.00069e+18,Fragrance,Estore,Dior,FR,Nice,46-60yo,2,Premium,31,Cooling,Promo Dependence,78.6,Elite,Premium Loyalists,1,1
-1.93741e+17,1735.48,1153.06,143,115,2025-01-06,2025-12-10,15.09113043478261,5.97,359.25,6,43,2,3,6,338,2.9649122807017543,1,0.39918436303461263,1,,,,,,,,,FR,26-35yo,genz,2,GOUSSAINVILLE,4,1,No Loyalty,Champions,2025-01-06,0.0,634.53,1735.48,1153.06,1,SKINCARE -> SKINCARE -> SKINCARE -> MAKE UP -> SKINCARE,estore -> estore -> estore -> estore -> estore,SEPHORA -> SEPHORA -> SEPHORA -> SEPHORA -> SEPHORA FAVORITES,1735.48,582.4200000000001,0,-1.93741e+17,Skincare,Estore,Sephora,FR,Goussainville,26-35yo,2,Premium,21,Active,Promo Dependence,80.2,Elite,Premium Loyalists,1,1
5.9848e+18,1059.03,494.96999999999997,21,3,2025-01-21,2025-07-12,353.01,412.5,526.98,1,12,2,2,3,172,86.0,1,0.3185135135135135,1,,,,,,,,,FR,,geny,1,FRANCONVILLE,3,1,Bronze,Champions,2025-02-14,24.0,532.05,1059.03,494.96999999999997,1,FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> estore,KENZO -> DIOR -> CACHAREL,1059.03,564.06,0,5.9848e+18,Fragrance,Store,Kenzo,FR,Franconville,Unknown,1,Premium,172,At Risk,Erosion,81.1,Elite,Discount Explorers,1,1
2.6347e+18,1218.78,658.81,25,11,2025-01-09,2025-12-06,110.79818181818182,61.2,435.0,5,17,2,3,2,331,33.1,1,0.35088065019519704,1,,,,,,,,,FR,15-25yo,gena,2,PARIS,4,1,No Loyalty,Champions,2025-03-21,71.0,501.42,1218.78,658.81,1,SKINCARE -> SKINCARE -> SKINCARE -> SKINCARE -> MAKE UP,Store -> estore -> Store -> Store -> estore,SISLEY -> FIRST AID BEAUTY -> PAULA'S CHOICE -> PAULA'S CHOICE -> MAC,1218.78,559.97,0,2.6347e+18,Skincare,Store,Sisley,FR,Paris,15-25yo,2,Premium,25,Active,Promo Dependence,77.0,Elite,Premium Loyalists,1,1
7.22661e+18,997.04,547.94,69,16,2025-01-08,2025-12-17,62.315,47.265,148.32999999999998,6,18,2,3,3,343,22.866666666666667,1,0.3546583127289674,1,,,,,,,,,FR,46-60yo,,2,WARMERIVILLE,4,1,No Loyalty,Champions,2025-01-08,0.0,81.1,997.04,547.94,1,SKINCARE -> SKINCARE -> SKINCARE -> MAEK UP -> SKINCARE,Store -> Store -> Store -> Store -> estore,SEPHORA -> SUPERGOOP -> SEPHORA -> SEPHORA -> SEPHORA,997.04,449.0999999999999,0,7.22661e+18,Skincare,Store,Sephora,FR,Warmeriville,46-60yo,2,Premium,14,Active,Promo Dependence,80.3,Elite,Premium Loyalists,1,1
7.88502e+18,739.46,327.4,14,8,2025-01-08,2025-12-29,92.4325,114.155,192.0,4,6,1,2,2,355,50.714285714285715,1,0.3068818776596741,0,,,,,,,,,FR,m60yo,babyboomers,2,MONTBAZENS,4,1,No Loyalty,Champions,2025-01-22,14.0,242.82,739.46,327.4,1,MAEK UP -> MAEK UP -> FRAGRANCE -> FRAGRANCE -> FRAGRANCE,Store -> Store -> Store -> Store -> Store,SEPHORA -> LANCOME -> GUERLAIN -> CLARINS -> DIOR,739.46,412.06000000000006,0,7.88502e+18,Make Up,Store,Sephora,FR,Montbazens,m60yo,2,Premium,2,Active,Promo Dependence,73.4,Strong,Premium Loyalists,0,0
1.11085e+18,715.3199999999999,312.56,32,15,2025-01-04,2025-12-25,47.687999999999995,33.0,142.82999999999998,5,18,2,3,3,355,25.357142857142858,1,0.30408218858232483,1,,,,,,,,,FR,26-35yo,genz,2,STRASBOURG,4,1,No Loyalty,Champions,2025-01-04,0.0,429.29,715.3199999999999,312.56,1,MAKE UP -> MAKE UP -> MAKE UP -> SKINCARE -> MAEK UP,estore -> Store -> estore -> estore -> estore,KVD VEGAN BEAUTY -> RARE BEAUTY -> BENEFIT -> SEPHORA -> BENEFIT,715.3199999999999,402.75999999999993,0,1.11085e+18,Make Up,Estore,Kvd Vegan Beauty,FR,Strasbourg,26-35yo,2,Premium,6,Active,Promo Dependence,79.7,Elite,Premium Loyalists,1,1
-7.64622e+17,698.0,300.0,2,2,2025-09-16,2025-09-16,349.0,349.0,349.0,1,1,1,1,1,0,0.0,1,0.30060120240480964,0,,,,,,,,,FR,46-60yo,,2,VENTABREN,2,5,Silver,Promising,2025-09-16,0.0,698.0,698.0,300.0,1,HAIRCARE -> HAIRCARE,estore -> estore,DYSON -> DYSON,698.0,398.0,0,-7.64622e+17,Haircare,Estore,Dyson,FR,Ventabren,46-60yo,2,Premium,106,At Risk,Erosion,81.7,Elite,Discount Explorers,1,1
```
