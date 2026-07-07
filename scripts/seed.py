"""
Populate the database with the same catalogue the frontend ships as its
offline fallback data, so a freshly-deployed backend serves real content
immediately (see tubura_i18n.html: PRODUCT_BASE / PRODUCT_STRINGS,
TRAINING_BASE / TRAINING_STRINGS, FB_RETAILERS).

Run with:  python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.retailer import Retailer
from app.models.training import Training

PRODUCTS = [
    dict(
        category_key="Seeds", price=4500, stock=200, rating=4.8, sold=1500, img="maize-seeds.jpg",
        name_en="Maize Seeds (H614D)", name_rw="Mbuto za Kalamusi (H614D)", name_fr="Semences Maïs (H614D)",
        category_en="Seeds", category_rw="Imbuto", category_fr="Semences",
        unit_en="per 2kg pack", unit_rw="ku gasaho ka 2kg", unit_fr="par sac 2kg",
        description_en="High-yield hybrid. Drought tolerant. 110-day maturity. OAF-certified for Rwanda highlands.",
        description_rw="Umeze w'imbaraga. Birinda inzara. Iminsi 110. Byemejwe na OAF ku misozi y'u Rwanda.",
        description_fr="Hybride à haut rendement. Tolérant à la sécheresse. 110 jours. Certifié OAF pour les hautes terres rwandaises.",
    ),
    dict(
        category_key="CashCrops", price=200, stock=500, rating=4.9, sold=3400, img="coffee-seedlings.jpg",
        name_en="Coffee Seedlings", name_rw="Inzuki z'Ikawa", name_fr="Plants de Café",
        category_en="Cash Crops", category_rw="Imyaka Iterwa", category_fr="Cultures de rente",
        unit_en="per seedling", unit_rw="ku nzuki", unit_fr="par plant",
        description_en="Bourbon variety, ideal for Rwanda highlands. OAF-certified. Fruiting in 2–3 years.",
        description_rw="Ubwoko bwa Bourbon, bwiza ku misozi y'u Rwanda. Byemejwe na OAF. Ibikorwa mu myaka 2–3.",
        description_fr="Variété Bourbon, idéale pour les hautes terres. Certifié OAF. Fructification en 2–3 ans.",
    ),
    dict(
        category_key="Inputs", price=22000, stock=85, rating=4.7, sold=780, img="dap-fertilizer.jpg",
        name_en="DAP Fertilizer", name_rw="Ifumbire DAP", name_fr="Engrais DAP",
        category_en="Inputs", category_rw="Intete", category_fr="Intrants",
        unit_en="per 50kg bag", unit_rw="ku gasaho ka 50kg", unit_fr="par sac 50kg",
        description_en="Diammonium phosphate. Ideal for basal application. Season A planting input.",
        description_rw="Diammonium phosphate. Irimo muri basal. Ifumbire yo gutera Sezonyi A.",
        description_fr="Diammonium phosphate. Idéal en application de base. Intrant de plantation Saison A.",
    ),
    dict(
        category_key="Inputs", price=18000, stock=72, rating=4.6, sold=640, img="can-fertilizer.jpg",
        name_en="CAN Fertilizer", name_rw="Ifumbire CAN", name_fr="Engrais CAN",
        category_en="Inputs", category_rw="Intete", category_fr="Intrants",
        unit_en="per 50kg bag", unit_rw="ku gasaho ka 50kg", unit_fr="par sac 50kg",
        description_en="Calcium Ammonium Nitrate 26%. Top-dressing for maize and beans.",
        description_rw="Calcium Ammonium Nitrate 26%. Ikoreshwa ku buso bw'ibigori n'ibishyimbo.",
        description_fr="Nitrate de calcium et d'ammonium 26%. Amendement pour maïs et haricots.",
    ),
    dict(
        category_key="Seeds", price=2800, stock=160, rating=4.7, sold=920, img="bean-seeds-rwr2245.jpg",
        name_en="Bean Seeds (RWR 2245)", name_rw="Imbuto z'Ibishyimbo (RWR 2245)", name_fr="Semences Haricot (RWR 2245)",
        category_en="Seeds", category_rw="Imbuto", category_fr="Semences",
        unit_en="per 1kg pack", unit_rw="ku gasaho ka 1kg", unit_fr="par sac 1kg",
        description_en="Climbing bean. High yield, excellent market price. Rwanda-approved variety.",
        description_rw="Ibishyimbo biirukanwa. Umusaruro mwinshi, igiciro cyiza. Byemejwe mu Rwanda.",
        description_fr="Haricot grimpant. Haut rendement, excellent prix de marché. Variété approuvée au Rwanda.",
    ),
    dict(
        category_key="Trees", price=300, stock=400, rating=4.8, sold=1100, img="grevillea-seedlings.jpg",
        name_en="Grevillea Seedlings", name_rw="Inzuki za Grevillea", name_fr="Plants Grevillea",
        category_en="Trees", category_rw="Ibiti", category_fr="Arbres",
        unit_en="per seedling", unit_rw="ku nzuki", unit_fr="par plant",
        description_en="Agroforestry tree. Adds nitrogen to soil. OAF-recommended for soil health.",
        description_rw="Igiti cy'ubuhinzi buhuriweho. Kongereza azote mu butaka. Igisubizo gisa na OAF.",
        description_fr="Arbre agroforestier. Fixe l'azote dans le sol. Recommandé OAF pour la santé des sols.",
    ),
    dict(
        category_key="Trees", price=800, stock=240, rating=4.8, sold=1200, img="avocado-seedling.jpg",
        name_en="Avocado Seedling", name_rw="Inzuki z'Avoka", name_fr="Plant Avocat",
        category_en="Trees", category_rw="Ibiti", category_fr="Arbres",
        unit_en="per seedling", unit_rw="ku nzuki", unit_fr="par plant",
        description_en="Hass variety, grafted. Disease resistant. Income in 3–4 years.",
        description_rw="Ubwoko bwa Hass, yatanywe. Irwanya indwara. Amafaranga mu myaka 3–4.",
        description_fr="Variété Hass, greffé. Résistant aux maladies. Revenus en 3–4 ans.",
    ),
    dict(
        category_key="Equipment", price=3500, stock=150, rating=4.7, sold=890, img="pics-storage-bags.jpg",
        name_en="PICS Storage Bags", name_rw="Amasaho ya PICS", name_fr="Sacs de Stockage PICS",
        category_en="Equipment", category_rw="Imikoreshereze", category_fr="Équipement",
        unit_en="per pack (3 bags)", unit_rw="ku gasaho (amasaho 3)", unit_fr="par lot (3 sacs)",
        description_en="Hermetic storage. Protects grain from weevils for 6+ months post-harvest.",
        description_rw="Kubika neza. Birinda inzoga mu birungo igihe cy'amezi 6+.",
        description_fr="Stockage hermétique. Protège les grains des charançons pendant 6+ mois.",
    ),
    dict(
        category_key="Inputs", price=3500, stock=90, rating=4.4, sold=310, img="pesticide-karate.jpg",
        name_en="Pesticide (Karate)", name_rw="Umuti wa Karate", name_fr="Pesticide (Karate)",
        category_en="Inputs", category_rw="Intete", category_fr="Intrants",
        unit_en="per 100ml", unit_rw="ku 100ml", unit_fr="par 100ml",
        description_en="Lambda-cyhalothrin 5%. For aphids, caterpillars, army worm.",
        description_rw="Lambda-cyhalothrin 5%. Kurwanya inzuki, imifu, umurarambwa.",
        description_fr="Lambda-cyhalothrine 5%. Pour pucerons, chenilles, légionnaire d'automne.",
    ),
    dict(
        category_key="Equipment", price=15000, stock=30, rating=4.5, sold=180, img="knapsack-sprayer.jpg",
        name_en="Knapsack Sprayer", name_rw="Pompe yo Gusenya Imiti", name_fr="Pulvérisateur à Dos",
        category_en="Equipment", category_rw="Imikoreshereze", category_fr="Équipement",
        unit_en="per unit", unit_rw="ku kimwe", unit_fr="par unité",
        description_en="16L capacity, ergonomic. Includes all fittings and nozzles.",
        description_rw="Ubunini bwa 16L, yoroshe. Irimo ibikoresho byose.",
        description_fr="Capacité 16L, ergonomique. Fourni avec tous les accessoires et buses.",
    ),
    dict(
        category_key="Seeds", price=6500, stock=120, rating=4.6, sold=450, img="irish-potato-seed.jpg",
        name_en="Irish Potato Seed", name_rw="Imbuto z'Ibirayi", name_fr="Semences Pomme de Terre",
        category_en="Seeds", category_rw="Imbuto", category_fr="Semences",
        unit_en="per 10kg pack", unit_rw="ku gasaho ka 10kg", unit_fr="par sac 10kg",
        description_en="Certified seed potato. High yield suited for Rwanda climate.",
        description_rw="Imbuto z'ibirayi zemewe. Umusaruro mwinshi, buhuje ikirere cy'u Rwanda.",
        description_fr="Plants certifiés. Haut rendement adapté au climat rwandais.",
    ),
    dict(
        category_key="Inputs", price=8500, stock=65, rating=4.8, sold=240, img="avocado-npk-pack.jpg",
        name_en="Avocado Fertilizer", name_rw="Ifumbire y'Avoka", name_fr="Engrais Avocat",
        category_en="Inputs", category_rw="Intete", category_fr="Intrants",
        unit_en="per pack", unit_rw="ku gasaho", unit_fr="par lot",
        description_en="Specially formulated NPK for avocado and fruit trees.",
        description_rw="NPK yateguwe ku buryo bwihariye ku voka no ku biti bibyara imbuto.",
        description_fr="NPK spécialement formulé pour avocatiers et arbres fruitiers.",
    ),
]

TRAININGS = [
    dict(icon="coffee", available=True, duration_en="3 hours", duration_rw="Amasaha 3", duration_fr="3 heures",
         title_en="Coffee Cultivation", title_rw="Guhinga Ikawa", title_fr="Culture du Café",
         desc_en="Planting, pruning, and harvesting coffee. OAF best practices.",
         desc_rw="Gutera, gukeba no kwimbura ikawa. Uburyo bwiza bwa OAF.",
         desc_fr="Plantation, taille et récolte du café. Bonnes pratiques OAF."),
    dict(icon="tree", available=True, duration_en="2 hours", duration_rw="Amasaha 2", duration_fr="2 heures",
         title_en="Tree Management", title_rw="Kubungabunga Ibiti", title_fr="Gestion des Arbres",
         desc_en="Grevillea agroforestry, avocado pruning and grafting basics.",
         desc_rw="Grevillea mu buhinzi, gukeba no gutanya avoka.",
         desc_fr="Agroforesterie Grevillea, taille et greffage d'avocatiers."),
    dict(icon="bug", available=True, duration_en="2 hours", duration_rw="Amasaha 2", duration_fr="2 heures",
         title_en="Pest Management", title_rw="Kurwanya Ibyonnyi", title_fr="Gestion des Nuisibles",
         desc_en="Identify and treat common crop pests. Karate application demo.",
         desc_rw="Kumenya no kuvura ibyonnyi bikunze kugaragara. Igikorwa cya Karate.",
         desc_fr="Identifier et traiter les ravageurs courants. Démonstration d'application Karate."),
    dict(icon="globe", available=False, duration_en="4 hours", duration_rw="Amasaha 4", duration_fr="4 heures",
         title_en="Soil Health", title_rw="Ubuzima bw'Ubutaka", title_fr="Santé du Sol",
         desc_en="Micro-dosing fertilizer, composting, integrated soil fertility management.",
         desc_rw="Ifumbire nto nto, compost, gucunga ubutaka neza.",
         desc_fr="Micro-dosage d'engrais, compostage, gestion intégrée de la fertilité des sols."),
    dict(icon="package", available=True, duration_en="2 hours", duration_rw="Amasaha 2", duration_fr="2 heures",
         title_en="Post-Harvest Storage", title_rw="Kubika Imyaka Neza", title_fr="Stockage Post-Récolte",
         desc_en="Reduce losses. PICS bag technique, drying, Actellic application.",
         desc_rw="Kugabanya uburara. Uburyo bwa PICS, kwumvisha, Actellic.",
         desc_fr="Réduire les pertes. Technique sac PICS, séchage, application Actellic."),
    dict(icon="sprout", available=True, duration_en="3 hours", duration_rw="Amasaha 3", duration_fr="3 heures",
         title_en="Seed Spacing", title_rw="Gushyira Imbuto ku Murongo", title_fr="Espacement des Semences",
         desc_en="OAF row-planting technique. Spacing sticks and fertilizer micro-dosing.",
         desc_rw="Uburyo bwa OAF bwo gutera mu mirongo. Inkoni zo kubara n'ifumbire nto nto.",
         desc_fr="Technique de plantation en lignes OAF. Bâtons d'espacement et micro-dosage d'engrais."),
]

RETAILERS = [
    dict(name="Mugisha Agri Shop", phone="+250788001001", district="Gasabo", latitude=-1.9441, longitude=30.0619, stock_level="High"),
    dict(name="Uwimana Farm Store", phone="+250788002002", district="Kicukiro", latitude=-1.9706, longitude=30.1044, stock_level="Medium"),
    dict(name="Kigali Seeds Center", phone="+250788003003", district="Nyarugenge", latitude=-1.9536, longitude=30.0605, stock_level="High"),
    dict(name="Nyabihu Agrovet", phone="+250788004004", district="Nyabihu", latitude=-1.6516, longitude=29.5206, stock_level="Low"),
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            for p in PRODUCTS:
                db.add(Product(**p))
            print(f"Seeded {len(PRODUCTS)} products")
        else:
            print("Products already seeded, skipping")

        if db.query(Training).count() == 0:
            for t in TRAININGS:
                db.add(Training(**t))
            print(f"Seeded {len(TRAININGS)} trainings")
        else:
            print("Trainings already seeded, skipping")

        if db.query(Retailer).count() == 0:
            for r in RETAILERS:
                db.add(Retailer(**r))
            print(f"Seeded {len(RETAILERS)} retailers")
        else:
            print("Retailers already seeded, skipping")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
