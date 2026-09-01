import json
import csv
import subprocess
import os
import sys
import datetime

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

now = datetime.datetime.now()
DATE_FORMATTED = f"{now.day} - {now.strftime('%b')} {now.year}"

PARTNERS = [
    {
        "partner": "Admazing Cloud",
        "pe": "Fernando Laguna",
        "sheet_id": "1ofym1wCiQW6kz0z-vewGIh_XQ72GzuwoiTFmS0GLRB0",
        "partner_ids": [
            "0014M00002NlVN0QAN",
            "0014M00002TEyhPQAT"
        ],
        "cert_pids": [
            "0014M00002NlVN0QAN",
            "0014M00002TEyhPQAT"
        ],
        "drp_keys": [
            "P20240920001"
        ],
        "default_pid": "0014M00002NlVN0QAN",
        "country": "Argentina / MCO",
        "tier_level": "Premier"
    },
    {
        "partner": "Algeiba Business Solutions",
        "pe": "Fernando Laguna",
        "sheet_id": "1cVqPG7f33IsKQ3702M_1YyzAMSm2UfjExFuRoHo9rRc",
        "partner_ids": [
            "0014M00001h31YIQAY",
            "0014M00001jQcppQAC",
            "0014M00001h32gOQAQ",
            "001Kf000010diABIAY"
        ],
        "cert_pids": [
            "0014M00001h31YIQAY",
            "0014M00001jQcppQAC",
            "0014M00001h32gOQAQ",
            "001Kf000010diABIAY"
        ],
        "drp_keys": [
            "P20220923016"
        ],
        "default_pid": "0014M00001h32gOQAQ",
        "country": "Argentina / MCO",
        "tier_level": "Premier"
    },
    {
        "partner": "BFS Ingeniería Aplicada",
        "pe": "Fernando Laguna",
        "sheet_id": "1sZlGmDoTeKj7WSbZZybw7hGYPV7ELAnCeprQAzD1WgU",
        "partner_ids": [
            "0014M00001h35dDQAQ",
            "0014M00001h37s3QAA"
        ],
        "cert_pids": [
            "0014M00001h35dDQAQ",
            "0014M00001h37s3QAA"
        ],
        "drp_keys": [
            "0014M00001h35dDQAQ",
            "0014M00001h37s3QAA"
        ],
        "default_pid": "0014M00001h35dDQAQ",
        "country": "Mexico / MCO",
        "tier_level": "Premier"
    },
    {
        "partner": "Rubik",
        "pe": "Fernando Laguna",
        "sheet_id": "12tvcHWz0q48DgSPZcGqQsQtGd36MnAk_bhQRx4u5axs",
        "partner_ids": [
            "0014M00001h3Ay3QAE",
            "0014M00001h35xNQAQ",
            "0014M00002ROupzQAD",
            "0014M00001h32BeQAI",
            "0014M00002LU7SJQA1",
            "0014M00002LM9DXQA1",
            "0014M00002GH3xjQAD",
            "0014M00001h35xxQAA",
            "0014M00002RQXE7QAP",
            "0014M00002RSBX5QAP",
            "001Kf000019zlsUIAQ",
            "0014M00001yTHnfQAG",
            "0014M00001yRzGmQAK",
            "0014M00001oXcWHQA0",
            "0014M00001h38E4QAI"
        ],
        "cert_pids": [
            "0014M00001h3Ay3QAE",
            "0014M00001h35xNQAQ",
            "0014M00002ROupzQAD",
            "0014M00001h32BeQAI",
            "0014M00002LU7SJQA1",
            "0014M00002LM9DXQA1",
            "0014M00002GH3xjQAD",
            "0014M00001h35xxQAA",
            "0014M00002RQXE7QAP",
            "0014M00002RSBX5QAP",
            "001Kf000019zlsUIAQ",
            "0014M00001yTHnfQAG",
            "0014M00001yRzGmQAK",
            "0014M00001oXcWHQA0",
            "0014M00001h38E4QAI"
        ],
        "drp_keys": [
            "0014M00001h3Ay3QAE",
            "0014M00001h35xNQAQ",
            "0014M00002ROupzQAD"
        ],
        "default_pid": "0014M00002RSBX5QAP",
        "country": "Chile / MCO",
        "tier_level": "Premier"
    },
    {
        "partner": "Super Software",
        "pe": "Fernando Laguna",
        "sheet_id": "1Z27kkt7CrAH_AnV1GYQ51MYQJIrKOutKPM2tHF-iYdQ",
        "partner_ids": [
            "0014M00001p45vjQAA"
        ],
        "cert_pids": [
            "0014M00001p45vjQAA"
        ],
        "drp_keys": [
            "0014M00001p45vjQAA"
        ],
        "default_pid": "0014M00001p45vjQAA",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Tigabytes",
        "pe": "Fernando Laguna",
        "sheet_id": "1SkQLFoP2BQouGKutI5G14bxLiYZM4qsfM-Z30cj-unY",
        "partner_ids": [
            "0014M00001h39C2QAI",
            "0014M00001h32CTQAY",
            "0014M00001h38afQAA"
        ],
        "cert_pids": [
            "0014M00001h39C2QAI",
            "0014M00001h32CTQAY",
            "0014M00001h38afQAA"
        ],
        "drp_keys": [
            "P20220602092"
        ],
        "default_pid": "0014M00001h32CTQAY",
        "country": "Chile / Regional",
        "tier_level": "Premier"
    },
    {
        "partner": "Xertica",
        "pe": "Fernando Laguna",
        "sheet_id": "15t2IBgfMPcYUoQSXdRjjg8XCrM5jOu6qSgic5NzqUNs",
        "partner_ids": [
            "0014M00001h32ptQAA",
            "001Kf00001HDYb8IAH",
            "0014M00001h32DhQAI",
            "0014M000029TjdHQAS",
            "0014M000029WGRzQAO",
            "0014M00001h3Aw8QAE",
            "0014M00001h34zJQAQ",
            "0014M00001reUJRQA2",
            "0014M00001jjfBUQAY",
            "0014M00001h36EIQAY",
            "0014M00001h323oQAA",
            "0014M00002OSpJ8QAL"
        ],
        "cert_pids": [
            "0014M00001h32ptQAA",
            "001Kf00001HDYb8IAH",
            "0014M00001h32DhQAI",
            "0014M000029TjdHQAS",
            "0014M000029WGRzQAO",
            "0014M00001h3Aw8QAE",
            "0014M00001h34zJQAQ",
            "0014M00001reUJRQA2",
            "0014M00001jjfBUQAY",
            "0014M00001h36EIQAY",
            "0014M00001h323oQAA",
            "0014M00002OSpJ8QAL"
        ],
        "drp_keys": [
            "P20220428035"
        ],
        "default_pid": "0014M00001jjfBUQAY",
        "country": "Regional / LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "pe": "Ignacio Rauda",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "partner_ids": [
            "0014M00001h35nAQAQ",
            "0014M00001w6MZzQAM",
            "0014M00002M7ryLQAR",
            "001Kf000010ctuwIAA",
            "001Kf000010cw8CIAQ",
            "0014M00002N5mLOQAZ"
        ],
        "cert_pids": [
            "0014M00001h35nAQAQ",
            "0014M00001w6MZzQAM",
            "0014M00002M7ryLQAR",
            "001Kf000010ctuwIAA",
            "0014M00002N5mLOQAZ"
        ],
        "drp_keys": [
            "P20220923048",
            "0014M00001h35nAQAQ"
        ],
        "default_pid": "0014M00001h35nAQAQ",
        "country": "Regional / Spain & LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "Emergys Mexico",
        "pe": "Ignacio Rauda",
        "sheet_id": "1hikFFuQ0QpDgBY_FtnLcqHpUiASexgSGsPYrCZUNMY4",
        "partner_ids": [
            "0014M00001msBmRQAU"
        ],
        "cert_pids": [
            "0014M00001msBmRQAU"
        ],
        "drp_keys": [
            "P20220923099"
        ],
        "default_pid": "0014M00001msBmRQAU",
        "country": "Mexico",
        "tier_level": "Premier"
    },
    {
        "partner": "NXN Consultores",
        "pe": "Ignacio Rauda",
        "sheet_id": "1Tt1P5qe8P7Q3GETH1KOuGdCPsf-MBQKaMtDx3S20wIk",
        "partner_ids": [
            "0014M00001mrufoQAA",
            "001Kf00001GDi2WIAT",
            "0014M00001pbjpyQAA",
            "001Kf00001F9DzjIAF",
            "0014M00001h37J2QAI"
        ],
        "cert_pids": [
            "0014M00001mrufoQAA",
            "001Kf00001GDi2WIAT",
            "0014M00001pbjpyQAA",
            "001Kf00001F9DzjIAF",
            "0014M00001h37J2QAI"
        ],
        "drp_keys": [
            "P20230723037"
        ],
        "default_pid": "001Kf00001F9DzjIAF",
        "country": "Mexico",
        "tier_level": "Premier"
    },
    {
        "partner": "Nubosoft Servicios",
        "pe": "Ignacio Rauda",
        "sheet_id": "17eQt0Swei42yKenenPJ6Dq9jLEZR839BdnZMzfUMTNo",
        "partner_ids": [
            "001Kf00001CPDomIAH",
            "0014M00001h36arQAA",
            "0014M00002GIV9FQAX",
            "0014M00001uc5SvQAI"
        ],
        "cert_pids": [
            "001Kf00001CPDomIAH",
            "0014M00001h36arQAA",
            "0014M00002GIV9FQAX",
            "0014M00001uc5SvQAI"
        ],
        "drp_keys": [
            "P20220816024"
        ],
        "default_pid": "0014M00001h36arQAA",
        "country": "Mexico",
        "tier_level": "Premier"
    },
    {
        "partner": "U CLOUD STORE MÉXICO",
        "pe": "Ignacio Rauda",
        "sheet_id": "1nT3bjmJlDTCd1khZdzW1QRlL_f6aTFSw6z9yhfO2cls",
        "partner_ids": [
            "0014M00002JXkn6QAD"
        ],
        "cert_pids": [
            "0014M00002JXkn6QAD"
        ],
        "drp_keys": [
            "0014M00002JXkn6QAD"
        ],
        "default_pid": "0014M00002JXkn6QAD",
        "country": "Mexico",
        "tier_level": "Premier"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "pe": "Ignacio Rauda",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "partner_ids": [
            "0014M00002M7lcJQAR"
        ],
        "cert_pids": [
            "0014M00002M7lcJQAR"
        ],
        "drp_keys": [
            "0014M00002M7lcJQAR"
        ],
        "default_pid": "0014M00002M7lcJQAR",
        "country": "Colombia",
        "tier_level": "Premier"
    },
    {
        "partner": "Growth Partner Network (GPN)",
        "pe": "Ignacio Rauda, Fernando Laguna",
        "sheet_id": "1STeEh2SntjsXd-Ddse4YyBthPbWLql_bHB4HXIzRb2w",
        "partner_ids": [
            "0014M00002TEKP9QAP",
            "001Kf000012hAaiIAE",
            "001Kf00001E75n9IAB",
            "0014M00002NSez4QAD",
            "0014M00001tTpJzQAK",
            "001Kf00000wk9YCIAY",
            "0014M00001h3CbeQAE",
            "0014M00001h38bpQAA",
            "001Kf000019jA3IIAU",
            "0014M000020cUJuQAM",
            "001Kf00001DhFzAIAV"
        ],
        "cert_pids": [
            "0014M00002TEKP9QAP",
            "001Kf000012hAaiIAE",
            "001Kf00001E75n9IAB",
            "0014M00002NSez4QAD",
            "0014M00001tTpJzQAK",
            "001Kf00000wk9YCIAY",
            "0014M00001h3CbeQAE",
            "0014M00001h38bpQAA",
            "001Kf000019jA3IIAU",
            "0014M000020cUJuQAM",
            "001Kf00001DhFzAIAV"
        ],
        "drp_keys": [
            "0014M00002TEKP9QAP",
            "001Kf000012hAaiIAE",
            "001Kf00001E75n9IAB"
        ],
        "default_pid": "001Kf00001E75n9IAB",
        "country": "Mexico / Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Noventiq (Softline)",
        "pe": "Jaquelyn Montañez",
        "sheet_id": "1Rq5L7d_n1a34cTQGb8J-jHDejLcSdmnC18WLohWjsdU",
        "partner_ids": [
            "0014M00001h39APQAY",
            "0014M00001jtbqFQAQ",
            "0014M00001h34YXQAY",
            "0014M00002RRf3HQAT",
            "0014M00002RPO7QQAX",
            "0014M00001h3ARZQA2",
            "0014M00001h32gHQAQ",
            "0014M00001h323yQAA",
            "0014M00001h32p3QAA",
            "0014M00001h34xFQAQ",
            "0014M000026pzWLQAY",
            "0014M00001h355LQAQ"
        ],
        "cert_pids": [
            "0014M00001h39APQAY",
            "0014M00001jtbqFQAQ",
            "0014M00001h34YXQAY",
            "0014M00002RRf3HQAT",
            "0014M00002RPO7QQAX",
            "0014M00001h3ARZQA2",
            "0014M00001h32gHQAQ",
            "0014M00001h323yQAA",
            "0014M00001h32p3QAA",
            "0014M00001h34xFQAQ",
            "0014M000026pzWLQAY",
            "0014M00001h355LQAQ"
        ],
        "drp_keys": [
            "P20220923281",
            "0014M00001h39APQAY",
            "0014M00001jtbqFQAQ"
        ],
        "default_pid": "0014M00001h39APQAY",
        "country": "Chile / Regional LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "INFORMACIÓN LOCALIZADA SAS (Servinformación)",
        "pe": "Jaquelyn Montañez, Fernando Laguna",
        "sheet_id": "1H3cgdClncDnQDK9kY8s6U59jnfK_w4UmbE-z8dWexbs",
        "partner_ids": [
            "0014M00001h3AyDQAU",
            "0014M00001h34A7QAI",
            "0014M00002GHywFQAT",
            "0014M00002GHyqCQAT",
            "0014M00002TEROiQAP",
            "0014M00001w6OZ3QAM",
            "0014M00002NSRhUQAX",
            "001Kf000012gXIzIAM",
            "001Kf00001BCjQ0IAL",
            "0014M00002GHyyuQAD",
            "0014M00001jaT4bQAE",
            "0014M00001khC4uQAE",
            "0014M0000277PE9QAM"
        ],
        "cert_pids": [
            "0014M00001h3AyDQAU",
            "0014M00001h34A7QAI",
            "0014M00002GHywFQAT",
            "0014M00002GHyqCQAT",
            "0014M00002TEROiQAP",
            "0014M00001w6OZ3QAM",
            "0014M00002NSRhUQAX",
            "001Kf000012gXIzIAM",
            "001Kf00001BCjQ0IAL",
            "0014M00002GHyyuQAD",
            "0014M00001jaT4bQAE",
            "0014M00001khC4uQAE",
            "0014M0000277PE9QAM"
        ],
        "drp_keys": [
            "P20220602053",
            "0014M00001h3AyDQAU"
        ],
        "default_pid": "0014M00001h3AyDQAU",
        "country": "Colombia / Regional LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "Abacus Cambridge Partners",
        "pe": "Luna Longo",
        "sheet_id": "12MNfhjMKbal2luFR-gXwco1IlCfVjaCXO4YHlpPD8ms",
        "partner_ids": [
            "0014M00001mGcWKQA0",
            "001Kf000010dL7TIAU",
            "0014M00001h38C9QAI",
            "0014M00001jugzxQAA",
            "0014M00002QBWEPQA5",
            "0014M00001yT1CLQA0",
            "0014M00001pZodGQAS",
            "001Kf000012gWnrIAE",
            "0014M00001h30zAQAQ",
            "0014M00001h330TQAQ",
            "0014M00001p6fG1QAI",
            "001Kf00001Fp3btIAB",
            "0014M00001kwy81QAA",
            "0014M00001h398tQAA",
            "0014M00002JlwWeQAJ",
            "0014M00002JoF6IQAV",
            "0014M00001h39o5QAA",
            "0014M000026qUI8QAM",
            "0014M00002GGFn5QAH",
            "001Kf00001HFSjeIAH",
            "0014M00001sgH94QAE",
            "0014M00001h3CXCQA2",
            "0014M00001gwrpcQAA",
            "0014M00001tLDSGQA4"
        ],
        "cert_pids": [
            "0014M00001mGcWKQA0",
            "001Kf000010dL7TIAU",
            "0014M00001h38C9QAI",
            "0014M00001jugzxQAA",
            "0014M00002QBWEPQA5",
            "0014M00001yT1CLQA0",
            "0014M00001pZodGQAS",
            "001Kf000012gWnrIAE",
            "0014M00001h30zAQAQ",
            "0014M00001h330TQAQ",
            "0014M00001p6fG1QAI",
            "001Kf00001Fp3btIAB",
            "0014M00001kwy81QAA",
            "0014M00001h398tQAA",
            "0014M00002JlwWeQAJ",
            "0014M00002JoF6IQAV",
            "0014M00001h39o5QAA",
            "0014M000026qUI8QAM",
            "0014M00002GGFn5QAH",
            "001Kf00001HFSjeIAH",
            "0014M00001sgH94QAE",
            "0014M00001h3CXCQA2",
            "0014M00001gwrpcQAA",
            "0014M00001tLDSGQA4"
        ],
        "drp_keys": [
            "P20240324012",
            "P20231019004"
        ],
        "default_pid": "0014M00002GGFn5QAH",
        "country": "Regional / LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "Gentrop Cloud Brasil",
        "pe": "Luna Longo",
        "sheet_id": "1F9UbQ-kaBHELme9Feh4fQCdujXnC7hRhQX9tWzFD9WM",
        "partner_ids": [
            "001Kf00001FY2FRIA1",
            "0014M00001h32coQAA",
            "001Kf00001F93WNIAZ",
            "0014M000028FCl3QAG"
        ],
        "cert_pids": [
            "001Kf00001FY2FRIA1",
            "0014M00001h32coQAA",
            "001Kf00001F93WNIAZ",
            "0014M000028FCl3QAG"
        ],
        "drp_keys": [
            "P20220923132"
        ],
        "default_pid": "001Kf00001FY2FRIA1",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "QiNetwork",
        "pe": "Luna Longo",
        "sheet_id": "1rt85jLUA_r0KvNGO_wJD3qYfzPHA9nl5w2bw2sqOO8s",
        "partner_ids": [
            "0014M00001h3BemQAE",
            "0014M00001h30rmQAA"
        ],
        "cert_pids": [
            "0014M00001h3BemQAE",
            "0014M00001h30rmQAA"
        ],
        "drp_keys": [
            "P20220923242"
        ],
        "default_pid": "0014M00001h3BemQAE",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "Safetec Informática",
        "pe": "Luna Longo",
        "sheet_id": "1pfmHXAokv-KljvWUvHYL334NJpGpQK3jmPe9lxNzIng",
        "partner_ids": [
            "001Kf00001HWbTPIA1",
            "0014M00001h327IQAQ",
            "0014M00001qNF4FQAW"
        ],
        "cert_pids": [
            "001Kf00001HWbTPIA1",
            "0014M00001h327IQAQ",
            "0014M00001qNF4FQAW"
        ],
        "drp_keys": [
            "P20220923269"
        ],
        "default_pid": "0014M00001qNF4FQAW",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "pe": "Luna Longo",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "partner_ids": [
            "0014M00001uFlbSQAS",
            "0014M00002C1I0PQAV"
        ],
        "cert_pids": [
            "0014M00001uFlbSQAS",
            "0014M00002C1I0PQAV"
        ],
        "drp_keys": [
            "P20220602104",
            "0014M00001uFlbSQAS"
        ],
        "default_pid": "0014M00001uFlbSQAS",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "Comercializadora Zenta Group SPA",
        "pe": "Oliver Hartley",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "partner_ids": [
            "0014M00001h39BLQAY",
            "0014M00001m9woLQAQ",
            "001Kf000012gqs3IAA"
        ],
        "cert_pids": [
            "0014M00001h39BLQAY",
            "0014M00001m9woLQAQ",
            "001Kf000012gqs3IAA"
        ],
        "drp_keys": [
            "P20220602109",
            "0014M00001h39BLQAY",
            "0014M00001m9woLQAQ"
        ],
        "default_pid": "0014M00001h39BLQAY",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "pe": "Oliver Hartley",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "partner_ids": [
            "001Kf000013fuVXIAY",
            "001Kf00001FoCy9IAF"
        ],
        "cert_pids": [
            "001Kf000013fuVXIAY",
            "001Kf00001FoCy9IAF"
        ],
        "drp_keys": [
            "001Kf000013fuVXIAY",
            "001Kf00001FoCy9IAF"
        ],
        "default_pid": "001Kf000013fuVXIAY",
        "country": "El Salvador / Central America",
        "tier_level": "Premier"
    },
    {
        "partner": "Devaid SPA",
        "pe": "Oliver Hartley",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "partner_ids": [
            "0014M00001h38aiQAA",
            "0014M00001m9sVvQAI"
        ],
        "cert_pids": [
            "0014M00001h38aiQAA",
            "0014M00001m9sVvQAI"
        ],
        "drp_keys": [
            "P20220923084",
            "0014M00001h38aiQAA"
        ],
        "default_pid": "0014M00001h38aiQAA",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "MadeinWeb S/A",
        "pe": "Oliver Hartley",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "partner_ids": [
            "0014M00002GGNRCQA5",
            "001Kf000013hWaOIAU"
        ],
        "cert_pids": [
            "0014M00002GGNRCQA5",
            "001Kf000013hWaOIAU"
        ],
        "drp_keys": [
            "P20231208017",
            "0014M00002GGNRCQA5"
        ],
        "default_pid": "0014M00002GGNRCQA5",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "pe": "Oliver Hartley",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "partner_ids": [
            "001Kf0000150rJ2IAI",
            "0014M00001kxZPMQA2",
            "0014M00001m9v8HQAQ"
        ],
        "cert_pids": [
            "0014M00001kxZPMQA2",
            "001Kf0000150rJ2IAI",
            "0014M00001m9v8HQAQ"
        ],
        "drp_keys": [
            "P20220923297",
            "0014M00001kxZPMQA2",
            "001Kf0000150rJ2IAI"
        ],
        "default_pid": "0014M00001kxZPMQA2",
        "country": "Colombia / Regional",
        "tier_level": "Premier"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "pe": "Oliver Hartley",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "partner_ids": [
            "0014M00002JmizDQAR",
            "001Kf00001G4DmBIAV",
            "001Kf0000149iw9IAA"
        ],
        "cert_pids": [
            "0014M00002JmizDQAR",
            "001Kf00001G4DmBIAV",
            "001Kf0000149iw9IAA"
        ],
        "drp_keys": [
            "P20260318001",
            "0014M00002JmizDQAR"
        ],
        "default_pid": "0014M00002JmizDQAR",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "IPNET (Telefônica Cloud)",
        "pe": "Thiago da Ponte",
        "sheet_id": "1EpquIz41xu7RZPl-Y4nd-jTRbEl3qdAd8hJ53xxpd4M",
        "partner_ids": [
            "0014M00002QBQ0KQAX",
            "0014M00001w5vdTQAQ",
            "0014M00001h38bpQAA",
            "001Kf00000wjtGuIAI",
            "001Kf00001FlqhtIAB",
            "0014M00001h3BeiQAE",
            "0014M00001jSgzAQAS",
            "001Kf00001F7VMgIAN",
            "0014M00001pQmCHQA0",
            "001Kf000013fEbPIAU",
            "0014M00001yStvdQAC",
            "001Kf00001FlzzdIAB",
            "0014M00001h36IMQAY",
            "0014M00002C0zA3QAJ",
            "0014M00001h31NNQAY",
            "0014M000026rVKtQAM",
            "0014M00001h30r8QAA",
            "001Kf00001F8uDRIAZ",
            "001Kf00001F9FEzIAN",
            "0014M00002OSfuCQAT",
            "001Kf00001FlqhUIAR",
            "0014M00001jS0xGQAS",
            "0014M00001xhos3QAA"
        ],
        "cert_pids": [
            "0014M00002QBQ0KQAX",
            "0014M00001w5vdTQAQ",
            "0014M00001h38bpQAA",
            "001Kf00000wjtGuIAI",
            "001Kf00001FlqhtIAB",
            "0014M00001h3BeiQAE",
            "0014M00001jSgzAQAS",
            "001Kf00001F7VMgIAN",
            "0014M00001pQmCHQA0",
            "001Kf000013fEbPIAU",
            "0014M00001yStvdQAC",
            "001Kf00001FlzzdIAB",
            "0014M00001h36IMQAY",
            "0014M00002C0zA3QAJ",
            "0014M00001h31NNQAY",
            "0014M000026rVKtQAM",
            "0014M00001h30r8QAA",
            "001Kf00001F8uDRIAZ",
            "001Kf00001F9FEzIAN",
            "0014M00002OSfuCQAT",
            "001Kf00001FlqhUIAR",
            "0014M00001jS0xGQAS",
            "0014M00001xhos3QAA"
        ],
        "drp_keys": [
            "0014M00002QBQ0KQAX",
            "0014M00001w5vdTQAQ",
            "0014M00001h38bpQAA"
        ],
        "default_pid": "0014M00002C0zA3QAJ",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "Kyndryl Brasil",
        "pe": "Thiago da Ponte",
        "sheet_id": "1wvMK5gSOkTNl-oRS6XbvQJmrHDdz73tqKcGpF6DCZ2I",
        "partner_ids": [
            "0014M000026phCZQAY",
            "0014M00001pQ1mpQAC",
            "0014M00002F5JiGQAV",
            "001Kf00001HCncSIAT",
            "0014M00002BTRuoQAH",
            "001Kf00001FoCSrIAN",
            "0014M00002N6J8FQAV",
            "001Kf00001I6eFgIAJ",
            "0014M00001yTraMQAS",
            "001Kf00001I4lprIAB",
            "0014M000026pjkGQAQ",
            "001Kf00001HpoitIAB",
            "0014M00002RQuEmQAL",
            "0014M00002RQsxsQAD",
            "0014M0000282WpAQAU",
            "0014M00002BSo9qQAD",
            "0014M0000281YiqQAE",
            "0014M000026qh8oQAA",
            "0014M00002LRtwaQAD",
            "0014M00002BR5AuQAL",
            "001Kf000010co7uIAA",
            "001Kf00001I4b5qIAB",
            "001Kf00001FWTPMIA5",
            "0014M000026pffFQAQ",
            "0014M0000281B4tQAE",
            "0014M00002BT1J1QAL",
            "0014M00002GH8F5QAL",
            "0014M00002M9ldfQAB",
            "0014M000026rFcfQAE",
            "0014M00002KNyHbQAL",
            "0014M00002PLp8IQAT",
            "001Kf00001FpFXoIAN",
            "001Kf00001FmIOoIAN",
            "001Kf00001HqsIiIAJ",
            "001Kf00001I6DseIAF",
            "001Kf000010co8dIAA",
            "001Kf00001Hpn6UIAR",
            "0014M00002JnwanQAB",
            "0014M000026pZzVQAU",
            "0014M00002BSnwlQAD",
            "001Kf00001FYn0eIAD",
            "0014M00002Jmoh2QAB",
            "0014M000026pgeHQAQ",
            "0014M000026qa9PQAQ",
            "0014M00002RSD9UQAX",
            "0014M00002Jko6cQAB",
            "0014M00002C1zxYQAR",
            "0014M00002DKk7rQAD",
            "0014M000026pZF7QAM",
            "001Kf00001EyRZ8IAN",
            "0014M00002BRVhgQAH",
            "0014M00002803caQAA",
            "0014M000027zF5oQAE",
            "0014M000026pgkzQAA",
            "0014M000026phE6QAI",
            "001Kf00001HqyhkIAB",
            "0014M00002BTXwyQAH",
            "0014M00002BSnnDQAT",
            "0014M00002BSnvOQAT",
            "0014M00002C22r1QAB",
            "0014M00002BSnw7QAD",
            "001Kf00001I68KCIAZ",
            "0014M00002GH3tSQAT",
            "0014M00001yTakKQAS",
            "0014M00002BSkwLQAT",
            "0014M0000280G2vQAE",
            "001Kf00001I4b5lIAB",
            "0014M00001yTvhdQAC",
            "0014M00002CcfpGQAR",
            "001Kf00001HqYY4IAN",
            "0014M0000282g5JQAQ",
            "0014M00002NSHrCQAX",
            "0014M00002ROzRIQA1",
            "001Kf00001I6WPTIA3",
            "0014M00002C1M0OQAV",
            "0014M00002DKk5MQAT",
            "0014M00002LTHm2QAH",
            "0014M000025cA8GQAU",
            "0014M00002C0Vd7QAF",
            "0014M00002Byz9NQAR",
            "0014M0000282mM5QAI",
            "001Kf00001FXy1ZIAT",
            "0014M00002SxAh2QAF",
            "0014M00002BTsuJQAT",
            "001Kf00001HqUH8IAN",
            "001Kf00001H6eBgIAJ",
            "0014M00002C0F8qQAF",
            "001Kf00001H6pNHIAZ",
            "001Kf00001GBWmgIAH",
            "001Kf00001HqsIsIAJ",
            "001Kf00001H6bVYIAZ",
            "001Kf00000wiKmtIAE",
            "0014M00002RSEryQAH",
            "001Kf00001I75VaIAJ",
            "0014M00002Hx2X7QAJ",
            "0014M00002Bz6avQAB",
            "0014M00002Jm26jQAB",
            "0014M000026pwANQAY",
            "0014M000026pgQFQAY",
            "001Kf00001GCbmAIAT",
            "0014M00002OTbyXQAT",
            "0014M00001yUTa7QAG"
        ],
        "cert_pids": [
            "0014M000026phCZQAY",
            "0014M00001pQ1mpQAC",
            "0014M00002F5JiGQAV",
            "001Kf00001HCncSIAT",
            "0014M00002BTRuoQAH",
            "001Kf00001FoCSrIAN",
            "0014M00002N6J8FQAV",
            "001Kf00001I6eFgIAJ",
            "0014M00001yTraMQAS",
            "001Kf00001I4lprIAB",
            "0014M000026pjkGQAQ",
            "001Kf00001HpoitIAB",
            "0014M00002RQuEmQAL",
            "0014M00002RQsxsQAD",
            "0014M0000282WpAQAU",
            "0014M00002BSo9qQAD",
            "0014M0000281YiqQAE",
            "0014M000026qh8oQAA",
            "0014M00002LRtwaQAD",
            "0014M00002BR5AuQAL",
            "001Kf000010co7uIAA",
            "001Kf00001I4b5qIAB",
            "001Kf00001FWTPMIA5",
            "0014M000026pffFQAQ",
            "0014M0000281B4tQAE",
            "0014M00002BT1J1QAL",
            "0014M00002GH8F5QAL",
            "0014M00002M9ldfQAB",
            "0014M000026rFcfQAE",
            "0014M00002KNyHbQAL",
            "0014M00002PLp8IQAT",
            "001Kf00001FpFXoIAN",
            "001Kf00001FmIOoIAN",
            "001Kf00001HqsIiIAJ",
            "001Kf00001I6DseIAF",
            "001Kf000010co8dIAA",
            "001Kf00001Hpn6UIAR",
            "0014M00002JnwanQAB",
            "0014M000026pZzVQAU",
            "0014M00002BSnwlQAD",
            "001Kf00001FYn0eIAD",
            "0014M00002Jmoh2QAB",
            "0014M000026pgeHQAQ",
            "0014M000026qa9PQAQ",
            "0014M00002RSD9UQAX",
            "0014M00002Jko6cQAB",
            "0014M00002C1zxYQAR",
            "0014M00002DKk7rQAD",
            "0014M000026pZF7QAM",
            "001Kf00001EyRZ8IAN",
            "0014M00002BRVhgQAH",
            "0014M00002803caQAA",
            "0014M000027zF5oQAE",
            "0014M000026pgkzQAA",
            "0014M000026phE6QAI",
            "001Kf00001HqyhkIAB",
            "0014M00002BTXwyQAH",
            "0014M00002BSnnDQAT",
            "0014M00002BSnvOQAT",
            "0014M00002C22r1QAB",
            "0014M00002BSnw7QAD",
            "001Kf00001I68KCIAZ",
            "0014M00002GH3tSQAT",
            "0014M00001yTakKQAS",
            "0014M00002BSkwLQAT",
            "0014M0000280G2vQAE",
            "001Kf00001I4b5lIAB",
            "0014M00001yTvhdQAC",
            "0014M00002CcfpGQAR",
            "001Kf00001HqYY4IAN",
            "0014M0000282g5JQAQ",
            "0014M00002NSHrCQAX",
            "0014M00002ROzRIQA1",
            "001Kf00001I6WPTIA3",
            "0014M00002C1M0OQAV",
            "0014M00002DKk5MQAT",
            "0014M00002LTHm2QAH",
            "0014M000025cA8GQAU",
            "0014M00002C0Vd7QAF",
            "0014M00002Byz9NQAR",
            "0014M0000282mM5QAI",
            "001Kf00001FXy1ZIAT",
            "0014M00002SxAh2QAF",
            "0014M00002BTsuJQAT",
            "001Kf00001HqUH8IAN",
            "001Kf00001H6eBgIAJ",
            "0014M00002C0F8qQAF",
            "001Kf00001H6pNHIAZ",
            "001Kf00001GBWmgIAH",
            "001Kf00001HqsIsIAJ",
            "001Kf00001H6bVYIAZ",
            "001Kf00000wiKmtIAE",
            "0014M00002RSEryQAH",
            "001Kf00001I75VaIAJ",
            "0014M00002Hx2X7QAJ",
            "0014M00002Bz6avQAB",
            "0014M00002Jm26jQAB",
            "0014M000026pwANQAY",
            "0014M000026pgQFQAY",
            "001Kf00001GCbmAIAT",
            "0014M00002OTbyXQAT",
            "0014M00001yUTa7QAG"
        ],
        "drp_keys": [
            "P20220428047"
        ],
        "default_pid": "0014M00002LRtwaQAD",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "SantoDigital",
        "pe": "Thiago da Ponte",
        "sheet_id": "1F5uhnmaF-eEeWYGQRsoI8mU7brFRQjVye5gD7R8D50E",
        "partner_ids": [
            "0014M00001h328CQAQ",
            "0014M00001nkxtzQAA",
            "0014M00001rbdrUQAQ"
        ],
        "cert_pids": [
            "0014M00001h328CQAQ",
            "0014M00001nkxtzQAA",
            "0014M00001rbdrUQAQ"
        ],
        "drp_keys": [
            "P20220602085"
        ],
        "default_pid": "0014M00001h328CQAQ",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "Sauter Tecnologia",
        "pe": "Thiago da Ponte",
        "sheet_id": "1NKjJTPPOkss7UZIyE5G7LNdZydpICP20lfs0b4mS0LU",
        "partner_ids": [
            "0014M00002N6mbcQAB",
            "001Kf00001HrCZkIAN",
            "001Kf00001FXILGIA5",
            "001Kf00001GCHFEIA5",
            "001Kf00001GCCp4IAH",
            "001Kf00001HpumDIAR",
            "001Kf00001F9mHVIAZ",
            "001Kf00001HC49SIAT",
            "0014M00001mnmgxQAA",
            "001Kf00001HrFWAIA3",
            "001Kf00001F9ex4IAB",
            "001Kf000017JCwfIAG",
            "001Kf00001GCHRKIA5",
            "001Kf00001FotF1IAJ"
        ],
        "cert_pids": [
            "0014M00002N6mbcQAB",
            "001Kf00001HrCZkIAN",
            "001Kf00001FXILGIA5",
            "001Kf00001GCHFEIA5",
            "001Kf00001GCCp4IAH",
            "001Kf00001HpumDIAR",
            "001Kf00001F9mHVIAZ",
            "001Kf00001HC49SIAT",
            "0014M00001mnmgxQAA",
            "001Kf00001HrFWAIA3",
            "001Kf00001F9ex4IAB",
            "001Kf000017JCwfIAG",
            "001Kf00001GCHRKIA5",
            "001Kf00001FotF1IAJ"
        ],
        "drp_keys": [
            "P20220602086"
        ],
        "default_pid": "0014M00002N6mbcQAB",
        "country": "Brazil",
        "tier_level": "Premier"
    }
]

# 18 Columns for Partner Trackers (eliminates "Partner Name", includes "Workload Owner", "Workload Progress" to the right of "Workload Owner")
PARTNER_FOLLOWUP_HEADERS = [
    "Customer Account Name",            # Col 0 (A)
    "Account Tier",                     # Col 1 (B)
    "Workload Name",                    # Col 2 (C)
    "Workload Owner",                   # Col 3 (D)
    "Workload Progress",                # Col 4 (E)  <-- moved to right of Workload Owner
    "Capacity Status (DRP Readiness)",  # Col 5 (F)
    "Opportunity Name",                 # Col 6 (G)
    "Expert Requests",                  # Col 7 (H)
    "Customer Sub Region",              # Col 8 (I)
    "Customer Micro Region",            # Col 9 (J)
    "Primary Workload Pillar",          # Col 10 (K)
    "Sales Play",                       # Col 11 (L)
    "Workload Solution",                # Col 12 (M)
    "Begin Migration Date",             # Col 13 (N)
    "Production Date",                  # Col 14 (O)
    "Annual Gross Revenue (ARR USD)",   # Col 15 (P)
    "Last Touch",                       # Col 16 (Q)
    "Link"                              # Col 17 (R)
]

PARTNER_COL_WIDTHS = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 180,  # Workload Owner
    4: 170,  # Workload Progress
    5: 200,  # Capacity Status
    6: 260,  # Opportunity Name
    7: 180,  # Expert Requests
    8: 120,  # Customer Sub Region
    9: 130,  # Customer Micro Region
    10: 180, # Primary Workload Pillar
    11: 220, # Sales Play
    12: 220, # Workload Solution
    13: 130, # Begin Migration Date
    14: 130, # Production Date
    15: 150, # ARR USD
    16: 160, # Last Touch
    17: 160  # Link
}

# 19 Columns for Global Master Dashboard (preserves "Partner Name", includes "Workload Owner", "Workload Progress" to the right of "Workload Owner")
GLOBAL_FOLLOWUP_HEADERS = [
    "Partner Engineer (PE)",            # Col 0 (A)  <-- FIRST COLUMN
    "Partner Name",                     # Col 1 (B)
    "Customer Account Name",            # Col 2 (C)
    "Account Tier",                     # Col 3 (D)
    "Workload Name",                    # Col 4 (E)
    "Workload Owner",                   # Col 5 (F)
    "Workload Progress",                # Col 6 (G)
    "Capacity Status (DRP Readiness)",  # Col 7 (H)
    "Opportunity Name",                 # Col 8 (I)
    "Expert Requests",                  # Col 9 (J)
    "Customer Sub Region",              # Col 10 (K)
    "Customer Micro Region",            # Col 11 (L)
    "Primary Workload Pillar",          # Col 12 (M)
    "Sales Play",                       # Col 13 (N)
    "Workload Solution",                # Col 14 (O)
    "Begin Migration Date",             # Col 15 (P)
    "Production Date",                  # Col 16 (Q)
    "Annual Gross Revenue (ARR USD)",   # Col 17 (R)
    "Last Touch",                       # Col 18 (S)
    "Link"                              # Col 19 (T)
]

GLOBAL_COL_WIDTHS = {
    0: 160,  # Partner Engineer (PE)
    1: 250,  # Partner Name
    2: 280,  # Customer Account Name
    3: 90,   # Account Tier
    4: 240,  # Workload Name
    5: 180,  # Workload Owner
    6: 170,  # Workload Progress
    7: 200,  # Capacity Status
    8: 260,  # Opportunity Name
    9: 180,  # Expert Requests
    10: 120, # Customer Sub Region
    11: 130, # Customer Micro Region
    12: 180, # Primary Workload Pillar
    13: 220, # Sales Play
    14: 220, # Workload Solution
    15: 130, # Begin Migration Date
    16: 130, # Production Date
    17: 150, # ARR USD
    18: 160, # Last Touch
    19: 160  # Link
}

DRP_HEADERS = [
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]

GLOBAL_DRP_HEADERS = [
    "Partner Name",
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]

ACCRED_HEADERS = [
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
]

GLOBAL_ACCRED_HEADERS = [
    "Partner Name",
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
]

def make_hyperlink(url, label):
    if not url or not label:
        return label or ""
    clean_label = str(label).replace('"', '""')
    return f'=HYPERLINK("{url}", "{clean_label}")'

def parse_expert_requests(er_raw):
    if not er_raw or not isinstance(er_raw, dict):
        return ""
    f_list = er_raw.get("f", [])
    if not f_list:
        return ""
    items = f_list[0].get("v", [])
    if not items or not isinstance(items, list):
        return ""
    er_entries = []
    for item in items:
        val = item.get("v", {})
        if isinstance(val, dict) and "f" in val:
            fields = val["f"]
            er_name = fields[3].get("v") if len(fields) > 3 else ""
            er_id = fields[10].get("v") if len(fields) > 10 else ""
            if er_name:
                er_entries.append((er_name, er_id))
    if not er_entries:
        return ""
    if len(er_entries) == 1:
        name, er_id = er_entries[0]
        if er_id:
            return make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Expert_Request__c/{er_id}/view", name)
        return name
    else:
        return ", ".join([e[0] for e in er_entries])

def get_account_tier(segment_val):
    if not segment_val:
        return "3"
    s = str(segment_val).strip().lower()
    if "enterprise" in s or s == "1":
        return "1"
    elif "corporate" in s or s == "2":
        return "2"
    else:
        return "3"

def fetch_existing_manual_entries(ssid, tab_title="Follow_up"):
    manual_entries = {}
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, f"'{tab_title}'!A1:Z500", "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            if data and len(data) > 1:
                header_row_idx = -1
                lt_idx = -1
                link_idx = -1
                wkl_idx = -1
                for r_idx, row in enumerate(data):
                    for idx, h in enumerate(row):
                        h_clean = str(h).strip().lower()
                        if "workload name" in h_clean:
                            wkl_idx = idx
                            header_row_idx = r_idx
                        elif "last touch" in h_clean:
                            lt_idx = idx
                        elif "link" in h_clean:
                            link_idx = idx
                    if wkl_idx >= 0:
                        break
                if wkl_idx >= 0 and header_row_idx >= 0:
                    for row in data[header_row_idx + 1:]:
                        if len(row) > wkl_idx and row[wkl_idx]:
                            w_name = str(row[wkl_idx]).strip()
                            lt_val = str(row[lt_idx]).strip() if lt_idx >= 0 and len(row) > lt_idx else ""
                            link_val = str(row[link_idx]).strip() if link_idx >= 0 and len(row) > link_idx else ""
                            if lt_val or link_val:
                                manual_entries[w_name] = {"last_touch": lt_val, "link": link_val}
        except Exception as e:
            print(f"Error fetching manual entries for {ssid}: {e}")
    return manual_entries

def get_grid_info(ssid):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    data = json.loads(res.stdout)
    grid_info = {}
    for s in data.get("sheets", []):
        props = s.get("properties", {})
        grid_info[props.get("title")] = {
            "sheetId": props.get("sheetId", 0),
            "rowCount": props.get("gridProperties", {}).get("rowCount", 1000),
            "columnCount": props.get("gridProperties", {}).get("columnCount", 26)
        }
    return grid_info

def ensure_sheet_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    return None

def match_exact_drp(w_pillar, w_sales_play, w_solution, w_prods):
    w_pil_clean = (w_pillar or "").strip().lower()
    w_play_clean = (w_sales_play or "").strip().lower()
    w_sol_clean = (w_solution or "").strip().lower()
    w_prods_clean = [str(x).strip().lower() for x in (w_prods or [])]
    full_text = f"{w_pil_clean} {w_play_clean} {w_sol_clean} {' '.join(w_prods_clean)}"
    
    if "gemini enterprise" in full_text and ("workplace" in full_text or "licencias" in full_text or "seat" in full_text or "not a solution" in w_sol_clean or w_sol_clean == "gemini enterprise"):
        return [("Artificial Intelligence", "Agentic Workplace Transformation", "Gemini Enterprise")]
    
    if "gemini" in full_text and ("customer experience" in full_text or "ccaas" in full_text or "contact center" in full_text):
        return [("Artificial Intelligence", "Gemini Enterprise for Customer Experience", "Gemini Enterprise Agent Platform")]
        
    if "generative media" in full_text:
        return [("Artificial Intelligence", "Leverage Generative Media in your Business", "Gemini Enterprise Agent Platform")]
        
    if "your models" in full_text or "your business" in full_text:
        return [("Artificial Intelligence", "Your Business. Your Models.", "Gemini Enterprise Agent Platform")]
        
    if "ai apps" in full_text or "vertex" in full_text or "agent platform" in full_text or ("ai" in w_pil_clean and "agent" in full_text):
        return [("Artificial Intelligence", "Scale AI Apps and Agents", "Gemini Enterprise Agent Platform")]

    if "bigquery" in full_text or "warehouse" in full_text or "data analytics" in full_text or "analytics" in w_pil_clean:
        if "looker" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Looker")]
        elif "dataflow" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Dataflow")]
        elif "dataproc" in full_text or "spark" in full_text or "hadoop" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Dataproc")]
        else:
            return [("Data & Analytics", "The AI Ready Data Cloud", "BigQuery")]

    if "alloydb" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "AlloyDB for PostgreSQL")]
    if "cloud sql" in full_text or "postgres" in full_text or "mysql" in full_text or "sql server" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "Cloud SQL")]
    if "spanner" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "Spanner")]

    if "gke" in full_text or "kubernetes" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Google Kubernetes Engine")]
    if "cloud run" in full_text or "cloudrun" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Cloud Run")]
    if "apigee" in full_text or "api" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Apigee API Management")]

    if "vmware" in full_text or "gcve" in full_text:
        return [("Infrastructure Modernization", "Enterprise Platform of Choice: VMware", "Google Cloud VMware Engine")]
    if "mainframe" in full_text:
        return [("Infrastructure Modernization", "Mainframe Modernization", "Dual Run")]
    if "compute" in full_text or "gce" in full_text or "infra" in w_pil_clean or "infrastructure" in full_text:
        return [("Infrastructure Modernization", "Enterprise Infrastructure: Linux/Windows/Storage", "Compute Engine")]

    if "secops" in full_text or "chronicle" in full_text or "security" in full_text or "siem" in full_text or "soar" in full_text:
        return [("Security", "Modern SecOps", "Google Security Operations Enterprise (Chronicle SIEM)")]

    return [("Artificial Intelligence", "Scale AI Apps and Agents", "Gemini Enterprise Agent Platform")]

# 1. Fetch DRP Catalog
print("\n>>> Fetching full DRP Catalog from BigQuery...")
sql_catalog = """
SELECT DISTINCT
  pillar,
  sol as solution,
  COALESCE(p.scored_product, 'All Products') as product
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
CROSS JOIN UNNEST(p.parent_pillar) pillar
CROSS JOIN UNNEST(p.sales_play) sol
WHERE pillar IS NOT NULL AND sol IS NOT NULL
ORDER BY pillar, solution, product
"""
_, rows_cat = run_query(sql_catalog)
drp_catalog = [(r["f"][0].get("v"), r["f"][1].get("v"), r["f"][2].get("v")) for r in rows_cat]
print(f"Loaded {len(drp_catalog)} catalog products/solutions.")

os.makedirs("followup_data_latest", exist_ok=True)
os.makedirs("drp_data_latest", exist_ok=True)
os.makedirs("accred_data_latest", exist_ok=True)
os.makedirs("global_dashboard_data", exist_ok=True)

all_global_workload_rows = []
all_global_drp_rows = []
all_global_accred_rows = []
summary_stats = []

for cfg in PARTNERS:
    pname = cfg["partner"]
    pe_name = cfg.get("pe", "")
    ssid = cfg["sheet_id"]
    pids = ", ".join([f"'{x}'" for x in cfg["partner_ids"]])
    cert_pids_str = ", ".join([f"'{x}'" for x in cfg["cert_pids"]])
    drp_keys_str = ", ".join([f"'{x}'" for x in cfg["drp_keys"]])
    default_pid = cfg["default_pid"]
    safe_name = pname.replace(" ", "_").replace("(", "_").replace(")", "_").replace("/", "_").replace("&", "_")
    
    print(f"\n========================================================")
    print(f"Processing Partner: {pname} (PE: {pe_name})")
    print(f"Spreadsheet ID: {ssid}")
    print(f"========================================================")
    
    # A. DRP PROFILES QUERY
    sql_drp = f"""
    WITH Catalog AS (
      SELECT DISTINCT
        pillar,
        sol as solution,
        COALESCE(p.scored_product, 'All Products') as product
      FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
      CROSS JOIN UNNEST(p.parent_pillar) pillar
      CROSS JOIN UNNEST(p.sales_play) sol
      WHERE pillar IS NOT NULL AND sol IS NOT NULL
    ),
    PartnerProfiles AS (
      SELECT 
        p.consolidated_partner_id,
        pillar,
        sol as solution,
        COALESCE(p.scored_product, 'All Products') as product,
        COUNT(DISTINCT IF(p.tier_category = 'Tier 1', p.profile_id, NULL)) as tier1_count,
        COUNT(DISTINCT IF(p.tier_category = 'Tier 2', p.profile_id, NULL)) as tier2_count,
        COUNT(DISTINCT IF(p.tier_category IN ('Tier 1', 'Tier 2'), p.profile_id, NULL)) as total_tier1_tier2
      FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
      CROSS JOIN UNNEST(p.parent_pillar) pillar
      CROSS JOIN UNNEST(p.sales_play) sol
      WHERE p.consolidated_partner_id IN ({drp_keys_str})
      GROUP BY 1, 2, 3, 4
    )
    SELECT 
      c.pillar,
      c.solution,
      c.product,
      COALESCE(pp.tier1_count, 0) as tier1_count,
      COALESCE(pp.tier2_count, 0) as tier2_count,
      COALESCE(pp.total_tier1_tier2, 0) as total_tier1_tier2
    FROM Catalog c
    LEFT JOIN PartnerProfiles pp
      ON c.pillar = pp.pillar
      AND c.solution = pp.solution
      AND c.product = pp.product
    ORDER BY c.pillar, c.solution, c.product
    """
    _, drp_bq_rows = run_query(sql_drp)
    partner_drp_map = {}
    partner_total_drp_capacity = 0
    for r in drp_bq_rows:
        pil = r["f"][0].get("v")
        sol = r["f"][1].get("v")
        prd = r["f"][2].get("v")
        t1 = int(r["f"][3].get("v") or 0)
        t2 = int(r["f"][4].get("v") or 0)
        tot = int(r["f"][5].get("v") or 0)
        partner_drp_map[(pil, sol, prd)] = {"t1": t1, "t2": t2, "tot": tot}
        partner_total_drp_capacity += tot
        
    # B. WORKLOADS QUERY
    manual_entries = fetch_existing_manual_entries(ssid, "Follow_up")
    sql_wkl = f"""
    SELECT 
      w.workload_id,
      w.workload_name,
      w.opportunity_id,
      o.opportunity_name,
      COALESCE(w.sfdc_account_id, o.sfdc_account_id) AS sfdc_account_id,
      COALESCE(w.customer.account_name, o.account_name) AS account_name,
      COALESCE(w.customer.segment, o.segment) AS segment,
      COALESCE(w.customer.sub_region, o.sub_region) AS sub_region,
      COALESCE(w.customer.micro_region, o.micro_region) AS micro_region,
      w.workload_details.primary_workload_pillar,
      w.workload_details.sales_play,
      w.workload_details.workload_solutions,
      w.workload_details.workload_progress,
      CAST(w.workload_details.begin_migration_date AS STRING) AS begin_migration_date,
      CAST(w.workload_details.production_date AS STRING) AS production_date,
      w.metrics.annual_gross_revenue,
      w.expert_request,
      w.workload_details.partner_id,
      w.workload_details.partner_name,
      CAST(w.workload_details.sfdc_created_date AS STRING) AS sfdc_created_date,
      w.workload_details.key_workload_products,
      w.owner_details.owner_id,
      w.owner_details.owner_name
    FROM `concord-prod.service_cloudbi.workloads` w
    LEFT JOIN `concord-prod.service_cloudbi.opportunities` o
      ON w.opportunity_id = o.opportunity_id
    WHERE w.workload_details.partner_id IN ({pids})
      AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
      AND (w.workload_details.workload_progress IS NULL OR (
             LOWER(w.workload_details.workload_progress) NOT LIKE "%closed%"
             AND w.workload_details.workload_progress NOT LIKE "5.%"
          ))
      AND COALESCE(w.customer.segment, o.segment) != "Enterprise"
      AND IFNULL(o.is_commit, FALSE) = FALSE 
      AND IFNULL(o.forecast_category_name, "") != "Commit"
    ORDER BY w.workload_details.sfdc_created_date DESC, w.metrics.annual_gross_revenue DESC
    """
    _, wkl_bq_rows = run_query(sql_wkl)
    print(f"-> Uncommitted Workloads found: {len(wkl_bq_rows)}")
    
    drp_workload_demand = {(pil, sol, prd): 0 for (pil, sol, prd) in drp_catalog}
    partner_total_arr = 0.0
    
    partner_workload_rows = []
    for r in wkl_bq_rows:
        cells = r["f"]
        workload_id = cells[0].get("v") or ""
        workload_name = cells[1].get("v") or ""
        opportunity_id = cells[2].get("v") or ""
        opportunity_name = cells[3].get("v") or ""
        account_id = cells[4].get("v") or ""
        account_name = cells[5].get("v") or ""
        segment = cells[6].get("v") or ""
        sub_region = cells[7].get("v") or ""
        micro_region = cells[8].get("v") or ""
        pillar = cells[9].get("v") or ""
        sales_play = cells[10].get("v") or ""
        workload_solution = cells[11].get("v") or ""
        progress = cells[12].get("v") or ""
        begin_migration_date = cells[13].get("v") or ""
        production_date = cells[14].get("v") or ""
        arr_val = cells[15].get("v") or "0"
        er_raw = cells[16].get("v")
        row_partner_id = cells[17].get("v") or default_pid
        row_partner_name = cells[18].get("v") or pname
        key_prods_raw = cells[20].get("v") if len(cells) > 20 else []
        key_prods = [x.get("v") for x in key_prods_raw] if isinstance(key_prods_raw, list) else []
        owner_id = cells[21].get("v") if len(cells) > 21 else ""
        owner_name = cells[22].get("v") if len(cells) > 22 else ""
        
        try:
            arr_float = float(arr_val)
            partner_total_arr += arr_float
            arr_formatted = f"${arr_float:,.2f}"
        except:
            arr_formatted = "$0.00"
            
        p_url = f"https://vector.lightning.force.com/lightning/r/Account/{row_partner_id}/view" if row_partner_id else ""
        p_linked = make_hyperlink(p_url, row_partner_name) if p_url else row_partner_name
        
        acc_url = f"https://vector.lightning.force.com/lightning/r/Account/{account_id}/view" if account_id else ""
        acc_linked = make_hyperlink(acc_url, account_name) if acc_url else account_name
        
        wkl_url = f"https://vector.lightning.force.com/lightning/r/Workload__c/{workload_id}/view" if workload_id else ""
        wkl_linked = make_hyperlink(wkl_url, workload_name) if wkl_url else workload_name
        
        opp_url = f"https://vector.lightning.force.com/lightning/r/Opportunity/{opportunity_id}/view" if opportunity_id else ""
        opp_linked = make_hyperlink(opp_url, opportunity_name) if opp_url else opportunity_name
        
        er_linked = parse_expert_requests(er_raw)
        tier = get_account_tier(segment)
        
        matched_drp = match_exact_drp(pillar, sales_play, workload_solution, key_prods)
        for m_item in matched_drp:
            drp_workload_demand[m_item] = drp_workload_demand.get(m_item, 0) + 1
            
        total_drp_for_wkl = 0
        if matched_drp:
            total_drp_for_wkl = max([partner_drp_map.get(m, {}).get("tot", 0) for m in matched_drp])
            
        if total_drp_for_wkl == 0:
            wkl_capacity_status = "🔴 Capacity Gap (0 DRP Profiles)"
        elif total_drp_for_wkl == 1:
            wkl_capacity_status = "🟡 Constrained (1 DRP Profile)"
        else:
            wkl_capacity_status = f"🟢 Ready ({total_drp_for_wkl} DRP Profiles)"
            
        lt_preserved = ""
        link_preserved = ""
        if workload_name in manual_entries:
            lt_preserved = manual_entries[workload_name].get("last_touch", "")
            link_preserved = manual_entries[workload_name].get("link", "")
            
        # Partner table row: 18 columns (no partner column, includes Workload Owner at col 3, Workload Progress at col 4)
        row_followup = [
            acc_linked,             # 0: Customer Account Name
            tier,                   # 1: Account Tier
            wkl_linked,             # 2: Workload Name
            owner_name or "",       # 3: Workload Owner (plain text)
            progress,               # 4: Workload Progress
            wkl_capacity_status,    # 5: Capacity Status
            opp_linked,             # 6: Opportunity Name
            er_linked,              # 7: Expert Requests
            sub_region,             # 8: Sub Region
            micro_region,           # 9: Micro Region
            pillar,                 # 10: Pillar
            sales_play,             # 11: Sales Play
            workload_solution,      # 12: Workload Solution
            begin_migration_date,   # 13: Begin Migration Date
            production_date,        # 14: Production Date
            arr_formatted,          # 15: ARR USD
            lt_preserved,           # 16: Last Touch
            link_preserved          # 17: Link
        ]
        partner_workload_rows.append(row_followup)
        
        # Global table row: 20 columns (PE is Col 0, Partner Name is Col 1, followed by all 18 workload fields)
        global_row = [
            pe_name,                # 0: Partner Engineer (PE)
            p_linked,               # 1: Partner Name
            acc_linked,             # 2: Customer Account Name
            tier,                   # 3: Account Tier
            wkl_linked,             # 4: Workload Name
            owner_name or "",       # 5: Workload Owner (plain text)
            progress,               # 6: Workload Progress
            wkl_capacity_status,    # 7: Capacity Status
            opp_linked,             # 8: Opportunity Name
            er_linked,              # 9: Expert Requests
            sub_region,             # 10: Sub Region
            micro_region,           # 11: Micro Region
            pillar,                 # 12: Pillar
            sales_play,             # 13: Sales Play
            workload_solution,      # 14: Workload Solution
            begin_migration_date,   # 15: Begin Migration Date
            production_date,        # 16: Production Date
            arr_formatted,          # 17: ARR USD
            lt_preserved,           # 18: Last Touch
            link_preserved          # 19: Link
        ]
        all_global_workload_rows.append(global_row)
        
    # Top 5-row structured block for partner sheet (18 cols)
    partner_top_block = [
        ["Partner:", pname, "", "", "Last Update:", DATE_FORMATTED] + [""] * 12,
        [""] * 18,
        ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)"] + [""] * 10,
        [""] * 18,
        PARTNER_FOLLOWUP_HEADERS
    ]
    followup_rows = partner_top_block + partner_workload_rows
    followup_csv = os.path.join("followup_data_latest", f"{safe_name}_followup.csv")
    with open(followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)
        
    # Overwrite Tab 1: Follow_up
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True)
    
    # Get exact grid info
    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("Follow_up", {"sheetId": 0, "rowCount": len(followup_rows), "columnCount": 18})
    sid_followup = f_info["sheetId"]
    f_rows = f_info["rowCount"]
    
    # Freeze row 5 (header)
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)
    
    # Batch formatting for Follow_up
    batch_req = {
      "requests": [
        # Reset formatting
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18},
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"},
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "OVERFLOW_CELL"
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
          }
        },
        # Unmerge top rows
        {
          "unmergeCells": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": min(10, f_rows), "startColumnIndex": 0, "endColumnIndex": 18}
          }
        },
        # Merges
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        
        # Row 1 Format
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },

        # Row 3 Format (Light Purple for Alert Criteria)
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "LEFT"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 5 Main Header (Cols 0-15 Google Blue, Cols 16-17 Forest Green)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

        # Data Rows Formatting
        # Left-aligned text
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 13}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # Centered columns: Tier (Col 1), Capacity (Col 5), Dates (Cols 13-14)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 13, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # ARR Currency (Col 15)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 15, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        # Manual Note Columns (Cols 16-17)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

        # Hyperlinks (Cols 0, 2, 6)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

        # Borders
        {
          "updateBorders": {
            "range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18},
            "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
            "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
          }
        },
        # Basic Filter
        {"clearBasicFilter": {"sheetId": sid_followup}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}}}},

        # Conditional Formatting Rules (Progress is Col E [$E6], Production Date is Col O [$O6])
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}}}}, "index": 0}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=15, ($O6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}}}}, "index": 1}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=31, ($O6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}}}}, "index": 2}},

        # Row heights
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
      ]
    }
    
    # Zebra striping
    for r_idx in range(5, f_rows):
        if r_idx % 2 == 1:
            batch_req["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 16},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                    "fields": "userEnteredFormat(backgroundColor)"
                }
            })

    # Column widths
    for col_idx, width in PARTNER_COL_WIDTHS.items():
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Format ER column if has links
    for r_idx in range(5, f_rows):
        if r_idx < len(followup_rows):
            val = followup_rows[r_idx][7]
            if "ER-" in val and ("HYPERLINK" in val or "http" in val):
                batch_req["requests"].append({
                    "repeatCell": {
                        "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 7, "endColumnIndex": 8},
                        "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                    }
                })

    # Execute Batch Request
    tmp_batch = f"temp_batch_{ssid}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True)
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)
        
    # C. DRP STATUS TAB
    drp_rows = [DRP_HEADERS]
    for (pil, sol, prd) in drp_catalog:
        d_info = partner_drp_map.get((pil, sol, prd), {"t1": 0, "t2": 0, "tot": 0})
        t1_str = str(d_info["t1"]) if d_info["t1"] > 0 else ""
        t2_str = str(d_info["t2"]) if d_info["t2"] > 0 else ""
        tot_val = d_info["tot"]
        tot_str = str(tot_val) if tot_val > 0 else ""
        
        w_demand = drp_workload_demand.get((pil, sol, prd), 0)
        
        if w_demand > 0 and tot_val == 0:
            status_dot = f"🔴 Gap (0 DRP / {w_demand} wkls)"
        elif w_demand > 0 and tot_val < w_demand:
            status_dot = f"🟡 Constrained ({tot_val} DRP / {w_demand} wkls)"
        elif tot_val >= w_demand and (tot_val > 0 or w_demand > 0):
            status_dot = f"🟢 Ready ({tot_val} DRP / {w_demand} wkls)" if w_demand > 0 else f"🟢 Ready ({tot_val} profiles)"
        else:
            status_dot = "⚪ No Active Demand"
            
        drp_rows.append([pil, sol, prd, t1_str, t2_str, tot_str, status_dot])
        all_global_drp_rows.append([pname, pil, sol, prd, t1_str, t2_str, tot_str, status_dot])
        
    drp_csv = os.path.join("drp_data_latest", f"{safe_name}_drp.csv")
    with open(drp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drp_rows)
        
    tab_drp = "DRP_Status"
    sid_drp = ensure_sheet_tab(ssid, tab_drp)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_drp}'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_drp}'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, drp_csv, "--sheet", tab_drp], capture_output=True)
    
    # D. ACCREDITATIONS TAB
    sql_certs = f"""
    SELECT 
      p.certification_details.certification_name,
      p.certification_details.certification_type,
      p.certification_details.certification_sub_type,
      p.partner_contact_profile_details.profile_name,
      p.partner_contact_profile_details.lms_user_email,
      CAST(p.certification_details.certification_issued_date AS STRING) as issued_date,
      CAST(p.certification_details.certification_expiration_date AS STRING) as expiration_date,
      p.partner_details.partner_name
    FROM `concord-prod.service_cloudbi.partner_certifications` p
    WHERE p.partner_details.sfdc_partner_id IN ({cert_pids_str})
      AND p.reporting_month = (SELECT MAX(reporting_month) FROM `concord-prod.service_cloudbi.partner_certifications`)
    ORDER BY p.certification_details.certification_type, p.certification_details.certification_name, p.partner_contact_profile_details.profile_name
    """
    _, rows_certs = run_query(sql_certs)
    partner_total_certs = len(rows_certs)
    
    accred_rows = [ACCRED_HEADERS]
    if rows_certs:
        for r in rows_certs:
            cname = r["f"][0].get("v") or ""
            ctype = r["f"][1].get("v") or ""
            csubtype = r["f"][2].get("v") or ""
            pname_cand = r["f"][3].get("v") or ""
            pemail_cand = r["f"][4].get("v") or ""
            issued = r["f"][5].get("v") or ""
            exp = r["f"][6].get("v") or ""
            entity = r["f"][7].get("v") or ""
            accred_rows.append([cname, ctype, csubtype, pname_cand, pemail_cand, issued, exp, entity])
            all_global_accred_rows.append([pname, cname, ctype, csubtype, pname_cand, pemail_cand, issued, exp, entity])
    else:
        accred_rows.append(["No active accreditations found", "-", "-", "-", "-", "-", "-", "-"])
        all_global_accred_rows.append([pname, "No active accreditations found", "-", "-", "-", "-", "-", "-", "-"])
        
    accred_csv = os.path.join("accred_data_latest", f"{safe_name}_accred.csv")
    with open(accred_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(accred_rows)
        
    tab_accred = "Acreditaciones"
    sid_accred = ensure_sheet_tab(ssid, tab_accred)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_accred}'!A1:Z3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_accred}'!2:3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, accred_csv, "--sheet", tab_accred], capture_output=True)
    
    summary_stats.append({
        "pe": pe_name,
        "partner": pname,
        "country": cfg["country"],
        "track": cfg["tier_level"],
        "default_pid": default_pid,
        "sheet_id": ssid,
        "workloads_count": len(wkl_bq_rows),
        "total_arr": partner_total_arr,
        "drp_capacities": partner_total_drp_capacity,
        "certs_count": partner_total_certs
    })
    print(f"✓ Updated partner tracker for {pname} with Workload Owner column.")

# =========================================================================
# E. UPDATE GLOBAL PARTNER MANAGEMENT DASHBOARD
# =========================================================================
print("\n========================================================")
print("UPDATING GLOBAL PARTNER MANAGEMENT DASHBOARD")
print(f"Spreadsheet ID: {GLOBAL_SSID}")
print("========================================================")

# 1. Executive_Summary (9 columns: PE as Col 0)
summary_headers = [
    "Partner Engineer (PE)",
    "Partner Name",
    "Country / Headquarters",
    "Partner Advantage Track",
    "Uncommitted Tier 2 & 3 Workloads (#)",
    "Total Pipeline ARR ($ USD)",
    "DRP Profile Capacities (#)",
    "Active Accreditations / Certs (#)",
    "Partner Action Tracker Spreadsheet"
]
summary_rows = [summary_headers]
tot_all_wkls = sum(s["workloads_count"] for s in summary_stats)
tot_all_arr = sum(s["total_arr"] for s in summary_stats)
tot_all_drp = sum(s["drp_capacities"] for s in summary_stats)
tot_all_certs = sum(s["certs_count"] for s in summary_stats)

for s in summary_stats:
    p_url = f"https://vector.lightning.force.com/lightning/r/Account/{s['default_pid']}/view"
    p_link = make_hyperlink(p_url, s["partner"])
    tracker_url = f"https://docs.google.com/spreadsheets/d/{s['sheet_id']}/edit#gid=0"
    tracker_link = make_hyperlink(tracker_url, "Open Partner Tracker ↗")
    summary_rows.append([
        s["pe"],
        p_link,
        s["country"],
        s["track"],
        str(s["workloads_count"]),
        f"${s['total_arr']:,.2f}",
        str(s["drp_capacities"]),
        str(s["certs_count"]),
        tracker_link
    ])

summary_rows.append([
    f"TOTAL (All {len(PARTNERS)} Partners)",
    "-",
    "-",
    "-",
    str(tot_all_wkls),
    f"${tot_all_arr:,.2f}",
    str(tot_all_drp),
    str(tot_all_certs),
    "-"
])

exec_csv = "global_dashboard_data/executive_summary_latest.csv"
with open(exec_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(summary_rows)

sid_exec = ensure_sheet_tab(GLOBAL_SSID, "Executive_Summary")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'Executive_Summary'!A1:Z500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'Executive_Summary'!2:500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, exec_csv, "--sheet", "Executive_Summary"], capture_output=True)
if sid_exec is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_exec), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#1A73E8",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", str(len(summary_rows)-1), "--end-row", str(len(summary_rows)),
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#E8F0FE"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", "1", "--end-row", str(len(summary_rows)),
        "--start-col", "4", "--end-col", "8",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_exec), "--start-col", "0", "--end-col", "9"], capture_output=True)
print("✓ Updated Global Executive_Summary")

# 2. All_Workloads_Follow_up (20 cols, Global Top Block with PE as Col 0)
global_manual_entries = fetch_existing_manual_entries(GLOBAL_SSID, "All_Workloads_Follow_up")
for r in all_global_workload_rows:
    # r[4] is wkl_linked (Workload Name)
    w_name_plain = r[4]
    if '","' in w_name_plain:
        try:
            w_name_plain = w_name_plain.split('","')[1].rstrip('")')
        except:
            pass
    if w_name_plain in global_manual_entries:
        if not r[18]:
            r[18] = global_manual_entries[w_name_plain].get("last_touch", "")
        if not r[19]:
            r[19] = global_manual_entries[w_name_plain].get("link", "")

global_top_block = [
    ["Partner:", f"All {len(PARTNERS)} Partners (Global Management Dashboard)", "", "", "", "Last Update:", DATE_FORMATTED] + [""] * 13,
    [""] * 20,
    ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)"] + [""] * 12,
    [""] * 20,
    GLOBAL_FOLLOWUP_HEADERS
]
all_global_followup_rows = global_top_block + all_global_workload_rows
global_followup_csv = "global_dashboard_data/all_workloads_followup_latest.csv"
with open(global_followup_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_followup_rows)

sid_gwkl = ensure_sheet_tab(GLOBAL_SSID, "All_Workloads_Follow_up")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_followup_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)

grid_info_g = get_grid_info(GLOBAL_SSID)
gw_info = grid_info_g.get("All_Workloads_Follow_up", {"sheetId": sid_gwkl, "rowCount": len(all_global_followup_rows), "columnCount": 20})
sid_gwkl = gw_info["sheetId"]
gw_rows = gw_info["rowCount"]

subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_gwkl), "--rows", "5"], capture_output=True)

batch_req_g = {
  "requests": [
    # Reset
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
    {"unmergeCells": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": min(10, gw_rows), "startColumnIndex": 0, "endColumnIndex": 20}}},
    {"mergeCells": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 5}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
    
    # Row 1
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

    # Row 3 (Light Purple for Alert Criteria)
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

    # Row 5 Main Header
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 18, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

    # Data Rows Formatting
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 4, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 8, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    # Centered columns: Tier (Col 3), Capacity (Col 7), Dates (Cols 15-16)
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 15, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    # ARR Currency (Col 17)
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 17, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
    # Manual Note Columns (Cols 18-19)
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 18, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

    # Hyperlinks (Cols 1, 2, 4, 8)
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
    {"repeatCell": {"range": {"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 8, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

    # Borders
    {
      "updateBorders": {
        "range": {"sheetId": sid_gwkl, "startRowIndex": 4, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20},
        "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
      }
    },
    # Basic Filter
    {"clearBasicFilter": {"sheetId": sid_gwkl}},
    {"setBasicFilter": {"filter": {"range": {"sheetId": sid_gwkl, "startRowIndex": 4, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}}}},

    # Conditional Formatting Rules (Progress is Col G [$G6], Production Date is Col Q [$Q6])
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}}}}, "index": 0}},
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())>=15, ($Q6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}}}}, "index": 1}},
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_gwkl, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())>=31, ($Q6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}}}}, "index": 2}},

    # Row heights
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sid_gwkl, "dimension": "ROWS", "startIndex": 5, "endIndex": gw_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
  ]
}

# Zebra striping
for r_idx in range(5, gw_rows):
    if r_idx % 2 == 1:
        batch_req_g["requests"].append({
            "repeatCell": {
                "range": {"sheetId": sid_gwkl, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 18},
                "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                "fields": "userEnteredFormat(backgroundColor)"
            }
        })

# Column widths
for col_idx, width in GLOBAL_COL_WIDTHS.items():
    batch_req_g["requests"].append({
        "updateDimensionProperties": {
            "range": {"sheetId": sid_gwkl, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
            "properties": {"pixelSize": width},
            "fields": "pixelSize"
        }
    })

# Format ER column if has links
for r_idx in range(5, gw_rows):
    if r_idx < len(all_global_followup_rows):
        val = all_global_followup_rows[r_idx][9]
        if "ER-" in val and ("HYPERLINK" in val or "http" in val):
            batch_req_g["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": sid_gwkl, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 9, "endColumnIndex": 10},
                    "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                    "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                }
            })

tmp_batch_g = f"temp_batch_g_{GLOBAL_SSID}.json"
with open(tmp_batch_g, "w") as f:
    json.dump(batch_req_g, f)
subprocess.run([GSHEETS, "mutate", "raw-batch", GLOBAL_SSID, "-f", tmp_batch_g], capture_output=True)
if os.path.exists(tmp_batch_g):
    os.remove(tmp_batch_g)

print("✓ Updated Global All_Workloads_Follow_up with Workload Owner column.")

# 3. All_DRP_Status
global_drp_csv = "global_dashboard_data/all_drp_status_latest.csv"
with open(global_drp_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows([GLOBAL_DRP_HEADERS] + all_global_drp_rows)

sid_gdrp = ensure_sheet_tab(GLOBAL_SSID, "All_DRP_Status")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_DRP_Status'!A1:Z3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_DRP_Status'!2:3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_drp_csv, "--sheet", "All_DRP_Status"], capture_output=True)

# 4. All_Acreditaciones
global_accred_csv = "global_dashboard_data/all_accreditations_latest.csv"
with open(global_accred_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows([GLOBAL_ACCRED_HEADERS] + all_global_accred_rows)

sid_gaccred = ensure_sheet_tab(GLOBAL_SSID, "All_Acreditaciones")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Acreditaciones'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Acreditaciones'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_accred_csv, "--sheet", "All_Acreditaciones"], capture_output=True)

print("\n========================================================")
print("SUCCESS: ALL 10 SPREADSHEETS UPDATED WITH WORKLOAD OWNER COLUMN!")
print("========================================================")
