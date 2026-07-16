"""
Seed the fresh Tubura database with:
  1. Product categories (trilingual).
  2. All catalogue products (from the real product export).
  3. The first superadmin account (from ADMIN_USERNAME / ADMIN_PASSWORD env vars).

Stock is NOT seeded — it is per-retailer and entered in the dashboard after
you create your retailers.

Run with:  python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext

from app.db.session import SessionLocal
from app.models import Category, Administrator, Product

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

CATEGORIES = [
    dict(name_en="Seeds",                name_rw="Imbuto",                     name_fr="Semences",                 sort_order=1),
    dict(name_en="Fertilizers",          name_rw="Ifumbire",                   name_fr="Engrais",                  sort_order=2),
    dict(name_en="Pesticides",           name_rw="Imiti yica udukoko",         name_fr="Pesticides",               sort_order=3),
    dict(name_en="Farm Equipment",       name_rw="Ibikoresho by'ubuhinzi",     name_fr="Équipement agricole",      sort_order=4),
    dict(name_en="Gardening Supplies",   name_rw="Ibikoresho byo mu busitani", name_fr="Fournitures de jardinage", sort_order=5),
    dict(name_en="Animal Feed",          name_rw="Ibiribwa by'amatungo",       name_fr="Aliments pour animaux",    sort_order=6),
    dict(name_en="Veterinary Products",  name_rw="Imiti y'amatungo",           name_fr="Produits vétérinaires",    sort_order=7),
    dict(name_en="Irrigation Equipment", name_rw="Ibikoresho byo kuhira",      name_fr="Équipement d'irrigation",  sort_order=8),
    dict(name_en="Other Products",       name_rw="Ibindi bicuruzwa",           name_fr="Autres produits",          sort_order=9),
    dict(name_en="Trees",                name_rw="Ibiti",                      name_fr="Arbres",                   sort_order=10),
]

PRODUCTS = [
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Lemon seedling', 'name_rw': "Ingemwe y'Indimu", 'name_fr': 'Plant de Citronnier', 'price': 1.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Healthy lemon seedling suitable for establishing citrus orchards and home gardens.', 'description_rw': "Ingemwe nziza y'indimu igenewe guterwa mu mirima no mu busitani.", 'description_fr': "Plant sain de citronnier destiné aux vergers d'agrumes et aux jardins familiaux.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/lemon_seedling.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Plant in fertile, well-drained soil in a sunny location. Water regularly and care for the young tree until it is well established.', 'guide_rw': 'Tera mu butaka burumbuka kandi ahagera izuba. Vomerera buri gihe kandi wite ku giti kugeza gikuze neza.', 'guide_fr': "Planter dans un sol fertile et bien drainé dans un endroit ensoleillé. Arroser régulièrement jusqu'à la bonne installation du jeune plant."},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Orange Seedling', 'name_rw': "Ingemwe y'ironji", 'name_fr': "Plant d'Oranger", 'price': 1.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Healthy orange seedling suitable for establishing citrus orchards and home gardens.', 'description_rw': "Ingemwe nziza y'oranje igenewe guterwa mu mirima no mu busitani.", 'description_fr': "Plant sain d'oranger destiné aux vergers d'agrumes et aux jardins familiaux.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/orange_seedling.jpg', 'low_stock_threshold': 10, 'featured': False, 'status': 'active', 'guide_en': 'Plant in fertile, well-drained soil with adequate sunlight. Water regularly during establishment.', 'guide_rw': 'Tera mu butaka burumbuka kandi ahagera izuba. Vomerera buri gihe mu gihe ingemwe zigikura.', 'guide_fr': 'Planter dans un sol fertile et bien drainé avec une bonne exposition au soleil. Arroser régulièrement.'},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Mango Seedling', 'name_rw': "Ingemwe y'Umwembe", 'name_fr': 'Plant de Manguier', 'price': 1.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Healthy mango seedling suitable for establishing orchards and producing quality mango fruits.', 'description_rw': "Ingemwe nziza y'umwembe igenewe guterwa no gutanga umusaruro w'imyembe myiza.", 'description_fr': 'Plant sain de manguier destiné à produire des mangues de qualité.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/mango_seedling.jpg', 'low_stock_threshold': 10, 'featured': False, 'status': 'active', 'guide_en': 'Plant in fertile, well-drained soil with sufficient sunlight. Water regularly while the seedling establishes.', 'guide_rw': 'Tera mu butaka burumbuka kandi ahagera izuba. Vomerera buri gihe mu gihe ingemwe zigikura.', 'guide_fr': 'Planter dans un sol fertile et bien drainé exposé au soleil. Arroser régulièrement pendant la croissance.'},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Macadamia Seedling', 'name_rw': 'Ingemwe ya Makadamiya', 'name_fr': 'Plant de Macadamia', 'price': 1.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Healthy macadamia seedling suitable for establishing macadamia orchards and long-term nut production.', 'description_rw': "Ingemwe nziza ya makadamiya igenewe guterwa no gutangiza umurima wa makadamiya utanga umusaruro w'imbuto.", 'description_fr': "Plant sain de macadamia destiné à l'établissement de vergers et à la production durable de noix.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/macadamia.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Other Products', 'brand': None, 'name_en': 'Ground Coffee - 250 g', 'name_rw': 'Kawa Iseye -amagarama 250', 'name_fr': 'Café Moulu - 250 g', 'price': 1.0, 'unit_en': 'per pack', 'unit_rw': "kw' ipaki", 'unit_fr': 'par paquet', 'description_en': 'Ground coffee prepared for convenient brewing while retaining the aroma and character of Rwandan coffee.', 'description_rw': "Kawa iseye kandi iteguwe kugira ngo yorohereze kuyiteka, ibungabunge impumuro n'umwimerere wayo.", 'description_fr': 'Café moulu préparé pour faciliter la préparation tout en préservant son arôme et son caractère.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/ground_250.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Other Products', 'brand': None, 'name_en': 'Roasted Coffee - Brown 250 g', 'name_rw': 'Kawa Yokeje - Umukara - amagarama 250', 'name_fr': 'Café Torréfié - café noisette 250 g', 'price': 1.0, 'unit_en': 'per pack', 'unit_rw': 'ku paki', 'unit_fr': 'par paquet', 'description_en': 'Roasted coffee beans prepared to preserve the aroma and distinctive character of Rwandan coffee.', 'description_rw': "Kawa yokeje kandi iteguwe mu buryo bufasha kubungabunga impumuro n'umwimerere wa kawa y'u Rwanda.", 'description_fr': "Grains de café torréfiés et préparés pour préserver l'arôme et le caractère distinctif du café rwandais.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/roasted_250.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Farm Equipment', 'brand': None, 'name_en': 'Knapsack Sprayer', 'name_rw': 'Pompo yo Gutera Imiti', 'name_fr': 'Pulvérisateur à Dos', 'price': 15000.0, 'unit_en': 'per unit', 'unit_rw': 'kuri imwe', 'unit_fr': 'par unité', 'description_en': 'A backpack sprayer designed for applying agricultural crop protection products and other suitable farm solutions.', 'description_rw': "Pompo ihekwa mu mugongo ikoreshwa mu gutera imiti y'ibihingwa n'indi miti ikoreshwa mu buhinzi.", 'description_fr': "Pulvérisateur porté sur le dos conçu pour l'application de produits de protection des cultures.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/knapsack-sprayer.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Fill the tank with the prepared solution according to the product instructions. Secure the lid, wear appropriate protective equipment, and spray evenly. Clean the sprayer after use', 'guide_rw': 'Shyira umuti wateguwe muri pompo ukurikije amabwiriza. Funga neza, ambara ibikoresho byo kwirinda maze utere ku buryo bungana. Sukura pompo nyuma yo kuyikoresha.', 'guide_fr': 'Remplir le réservoir avec la solution préparée selon les instructions. Fermer correctement, porter un équipement de protection et pulvériser uniformément. Nettoyer après utilisation.'},
    {'category': 'Farm Equipment', 'brand': 'PICS', 'name_en': 'PICS Storage Bag', 'name_rw': 'Umufuka wo Guhunikamo PICS', 'name_fr': 'Sac de Stockage PICS', 'price': 3491.0, 'unit_en': 'par bag', 'unit_rw': 'ku muguka', 'unit_fr': 'par sac', 'description_en': 'A hermetic storage bag designed to protect harvested crops during storage.', 'description_rw': 'Umufuka wa PICS wagenewe guhunikamo umusaruro no kuwurinda mu gihe ubitswe.', 'description_fr': 'Sac hermétique conçu pour protéger les récoltes pendant le stockage.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/pics-storage-bags.jpg', 'low_stock_threshold': 10, 'featured': False, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Seeds', 'brand': None, 'name_en': 'Avocado Seedling', 'name_rw': "Ingemwe y'Avoka", 'name_fr': "Plant d'Avocatier", 'price': 799.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Avocado seedling suitable for planting and establishment of avocado trees.', 'description_rw': "Ingemwe y'avoka yagenewe guterwa no gukuramo igiti cy'avoka.", 'description_fr': "Plant d'avocatier destiné à la plantation et à l'établissement d'arbres fruitiers.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/avocado-seedling.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Plant in fertile, well-drained soil. Water after planting and provide regular care as the young tree establishes.', 'guide_rw': 'Tera mu butaka burumbuka kandi butarekamo amazi. Vomerera nyuma yo gutera kandi ukomeze kwita ku ngemwe.', 'guide_fr': 'Planter dans un sol fertile et bien drainé. Arroser après la plantation et entretenir régulièrement le jeune plant.'},
    {'category': 'Seeds', 'brand': None, 'name_en': 'RWR 2245 Bean Seeds', 'name_rw': "Imbuto y'Ibishyimbo RWR 2245", 'name_fr': 'Semences de Haricot RWR 2245', 'price': 2800.0, 'unit_en': 'per kg', 'unit_rw': 'ku kiro', 'unit_fr': 'par kg', 'description_en': 'RWR 2245 bean seeds intended for agricultural planting and bean production.', 'description_rw': "Imbuto y'ibishyimbo RWR 2245 yagenewe guterwa no gutanga umusaruro w'ibishyimbo.", 'description_fr': 'Semences de haricot RWR 2245 destinées à la plantation et à la production de haricots.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/bean-seeds-rwr2245.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Plant in well-prepared soil using recommended spacing. Follow local agricultural guidance for fertilizer application and crop management.', 'guide_rw': "Tera mu butaka bwateguwe neza kandi wubahirize intera ikwiye. Kurikiza inama z'ubuhinzi ku ikoreshwa ry'ifumbire no kwita ku gihingwa.", 'guide_fr': "Semer dans un sol bien préparé en respectant l'espacement recommandé. Suivre les conseils agricoles pour la fertilisation et l'entretien."},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Coffee Seedlings', 'name_rw': 'Ingemwe za Kawa', 'name_fr': 'Plants de Caféier', 'price': 200.0, 'unit_en': 'per seedling', 'unit_rw': 'ku ngemwe', 'unit_fr': 'par plant', 'description_en': 'Coffee seedlings prepared for planting and establishment of coffee farms.', 'description_rw': 'Ingemwe za kawa zagenewe guterwa no gushinga cyangwa kongera ubuhinzi bwa kawa.', 'description_fr': "Plants de caféier destinés à la plantation et à l'établissement de caféières.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/coffee-seedlings.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Large Potato Seed Tubers', 'name_rw': "Imbuto y'ibirayi Nini", 'name_fr': 'Gros Tubercules de Semence de Pomme de Terre', 'price': 855.0, 'unit_en': 'per kg', 'unit_rw': 'ku kiro', 'unit_fr': 'par kg', 'description_en': 'Large-sized potato seed tubers intended for planting and potato production.', 'description_rw': "Imbuto z'ibirayi nini zigenewe guterwa no gutanga umusaruro w'ibirayi.", 'description_fr': 'Gros tubercules de semence de pomme de terre destinés à la plantation et à la production de pommes de terre.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/ibirayi_big.jpg', 'low_stock_threshold': 10, 'featured': False, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Medium Potato Seed Tubers', 'name_rw': "Imbuto y'Ibirayi ziringaniye", 'name_fr': 'Tubercules Moyens de Semence de Pomme de Terre', 'price': 950.0, 'unit_en': 'per kg', 'unit_rw': 'ku kiro', 'unit_fr': 'par kg', 'description_en': 'Medium-sized potato seed tubers intended for planting and potato production.', 'description_rw': "Imbuto z'ibirayi ziciriritse zigenewe guterwa no gutanga umusaruro w'ibirayi.", 'description_fr': 'Tubercules moyens de semence de pomme de terre destinés à la plantation et à la production de pommes de terre.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/ibirayi_medium.jpg', 'low_stock_threshold': 10, 'featured': False, 'status': 'active', 'guide_en': 'Plant in well-prepared, fertile soil. Place seed tubers at the recommended spacing and cover with soil. Follow local agricultural guidance for fertilization and crop care.', 'guide_rw': "Tera mu butaka bwateguwe neza kandi burumbuka. Tera imbuto ku ntera ikwiye maze uzitwikirize ubutaka. Kurikiza inama z'ubuhinzi ku ifumbire no kwita ku gihingwa.", 'guide_fr': "Planter dans un sol fertile et bien préparé. Respecter l'espacement recommandé et couvrir les tubercules de terre. Suivre les recommandations agricoles locales."},
    {'category': 'Seeds', 'brand': 'Tubura', 'name_en': 'Small Potato Seed Tubers', 'name_rw': "Imbuto y'Ibirayi Nto", 'name_fr': 'Petits Tubercules de Semence de Pomme de Terre', 'price': 1000.0, 'unit_en': 'per kg', 'unit_rw': 'ku kiro', 'unit_fr': 'par kg', 'description_en': 'Small-sized potato seed tubers intended for planting and potato production.', 'description_rw': "Imbuto z'ibirayi nto zigenewe guterwa no gutanga umusaruro w'ibirayi.", 'description_fr': 'Petits tubercules de semence de pomme de terre destinés à la plantation et à la production de pommes de terre.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/ibirayi_small.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Farm Equipment', 'brand': None, 'name_en': 'Tarpaulin', 'name_rw': 'Shitingi', 'name_fr': 'Bâche', 'price': 22000.0, 'unit_en': 'per unit', 'unit_rw': 'kuri imwe', 'unit_fr': 'par unité', 'description_en': 'A durable tarpaulin suitable for drying crops, covering agricultural products, and protecting materials from the ground and weather.', 'description_rw': "Shitingi ikomeye ikoreshwa mu kwanika umusaruro, gutwikira ibikomoka ku buhinzi no kurinda ibikoresho ubutaka n'imvura.", 'description_fr': 'Une bâche résistante adaptée au séchage des récoltes, à la couverture des produits agricoles et à la protection des matériaux.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/shitingi.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Other Products', 'brand': None, 'name_en': 'Rondereza Improved Cookstove', 'name_rw': 'Rondereza', 'name_fr': 'Foyer Amélioré Rondereza', 'price': 10000.0, 'unit_en': 'per unit', 'unit_rw': 'kuri imwe', 'unit_fr': 'par unité', 'description_en': 'An improved cookstove designed to use firewood more efficiently and support cleaner, more convenient household cooking.', 'description_rw': 'Rondereza ni iziko rinoze rigenewe gukoresha inkwi neza no koroshya guteka mu rugo.', 'description_fr': 'Un foyer amélioré conçu pour utiliser le bois de chauffage plus efficacement et faciliter la cuisson domestique.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/rondereza.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Other Products', 'brand': 'GLP', 'name_en': 'GLP Pico Solar Kit', 'name_rw': "Kit y'Imirasire y'Izuba GLP Pico", 'name_fr': 'Kit Solaire GLP Pico', 'price': 7000.0, 'unit_en': 'per unit', 'unit_rw': 'kuri imwe', 'unit_fr': 'par unité', 'description_en': 'Compact solar lighting solution designed for basic household lighting needs.', 'description_rw': "Igikoresho gito gikoresha ingufu z'izuba kigenewe gutanga urumuri rw'ibanze mu rugo.", 'description_fr': "Solution solaire compacte conçue pour répondre aux besoins d'éclairage de base du ménage.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/GLP_pico_solar_kit.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': None, 'guide_rw': None, 'guide_fr': None},
    {'category': 'Other Products', 'brand': 'GLP', 'name_en': 'GLP SKP 200 Solar Kit', 'name_rw': "Kit y'Imirasire y'Izuba GLP SKP 200", 'name_fr': 'Kit Solaire GLP SKP 200', 'price': 17000.0, 'unit_en': 'per unit', 'unit_rw': 'kuri imwe', 'unit_fr': 'par unité', 'description_en': 'Solar energy kit designed to provide convenient lighting and basic household energy access.', 'description_rw': "Kit ikoresha ingufu z'izuba igenewe gutanga urumuri no gufasha mu bikenerwa by'ibanze by'ingufu mu rugo.", 'description_fr': "Kit d'énergie solaire conçu pour fournir un éclairage pratique et répondre aux besoins énergétiques de base du ménage.", 'img': 'https://sylvan655-oss.github.io/tubura-frontend/GLP_200_solar_kit.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Install the solar panel where it receives direct sunlight. Connect the system components according to the product instructions and charge before use.', 'guide_rw': "Shyira panneau solaire ahagera izuba neza. Huza ibice bya sisitemu ukurikije amabwiriza y'igikoresho kandi ubanze uyishyire ku muriro w'izuba.", 'guide_fr': 'Installer le panneau solaire dans un endroit bien exposé au soleil. Connecter les composants selon les instructions du produit et charger avant utilisation.'},
    {'category': 'Other Products', 'brand': 'Tubura', 'name_en': 'Travertine Grade 1', 'name_rw': 'Ishwagara icyiciro cya 1', 'name_fr': 'Travertin Grade 1', 'price': 130.0, 'unit_en': 'per kg', 'unit_rw': 'ku kiro', 'unit_fr': 'par kg', 'description_en': 'Grade 1 agricultural travertine used to improve soil conditions and support better crop production.', 'description_rw': 'Travertine yo mu cyiciro cya mbere ikoreshwa mu kunoza ubutaka no gufasha ibihingwa gukura neza.', 'description_fr': 'Travertin agricole de première qualité utilisé pour améliorer les conditions du sol et favoriser la production agricole.', 'img': 'https://sylvan655-oss.github.io/tubura-frontend/travertin.jpg', 'low_stock_threshold': 10, 'featured': True, 'status': 'active', 'guide_en': 'Apply according to the needs of your soil and crop. Follow agricultural guidance on the recommended application rate.', 'guide_rw': "Koresha ukurikije imiterere y'ubutaka n'igihingwa cyawe. Kurikiza inama z'ubuhinzi ku kigero gikwiye.", 'guide_fr': 'Appliquer selon les besoins du sol et de la culture. Suivre les recommandations agricoles concernant la quantité à utiliser.'},
]


def seed():
    db = SessionLocal()
    try:
        # ── Categories ────────────────────────────────────────────────────
        if db.query(Category).count() == 0:
            for c in CATEGORIES:
                db.add(Category(**c))
            db.commit()
            print(f"Seeded {len(CATEGORIES)} categories")
        else:
            print("Categories already exist, skipping")

        # map category name -> id
        cat_id = {c.name_en: c.id for c in db.query(Category).all()}

        # ── Products ──────────────────────────────────────────────────────
        if db.query(Product).count() == 0:
            n = 0
            for p in PRODUCTS:
                data = dict(p)
                cname = data.pop("category")
                cid = cat_id.get(cname)
                if not cid:
                    print(f"  ! category '{cname}' not found for {data['name_en']}, skipping")
                    continue
                db.add(Product(category_id=cid, **data))
                n += 1
            db.commit()
            print(f"Seeded {n} products")
        else:
            print("Products already exist, skipping")

        # ── First superadmin ─────────────────────────────────────────────
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")
        if not username or not password:
            print("WARNING: ADMIN_USERNAME / ADMIN_PASSWORD not set — "
                  "no admin account created.")
        elif db.query(Administrator).filter_by(username=username).first():
            print(f"Admin '{username}' already exists, skipping")
        else:
            db.add(Administrator(
                username=username,
                password_hash=pwd.hash(password),
                role="superadmin",
                permissions=["products", "categories", "retailers", "stock",
                             "orders", "preorders", "customers",
                             "notifications", "support", "admins"],
            ))
            db.commit()
            print(f"Created superadmin '{username}'")

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
