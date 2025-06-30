import argparse
import pandas as pd
import time
import random
import os
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import yagmail
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def construire_url(base_url, ville, type_bien, prix_max, pieces_min, page=1):
    params = {
        "category": "9",
        "real_estate_type": type_bien,  # 1: maison, 2: appartement
        "location": ville,
        "rooms": f"{pieces_min}-max",
        "price": f"min-{prix_max}",
        "page": page
    }
    return f"{base_url}?{urlencode(params)}"

def RecuperUrl(driver):
    urls = []
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[data-test-id='listing-column']")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        ul = soup.find("ul", {"data-test-id": "listing-column"})
        for li in ul.find_all("li"):
            a_tag = li.find("a", href=True)
            if a_tag:
                urls.append(urljoin("https://www.leboncoin.fr", a_tag["href"]))
    except Exception as e:
        print("Erreur dans RecuperUrl:", e)
    return urls

def RecuperTous(url, driver):
    driver.get(url)
    time.sleep(random.uniform(1, 2))
    data = {"url": url}
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        titre = soup.find("h1", {"data-qa-id": "adview_title"})
        if titre:
            data["titre"] = titre.text.strip()
        prix = soup.find("div", {"data-qa-id": "adview_price"})
        if prix:
            data["prix"] = prix.text.strip()
        desc = soup.find("div", {"data-qa-id": "adview_description_container"})
        if desc:
            data["description"] = desc.text.strip()
        loc = soup.find("p", class_="inline-flex")
        if loc:
            data["localisation"] = loc.text.strip()
        pub = soup.find("p", class_="text-caption text-neutral")
        if pub:
            data["date_publication"] = pub.text.strip()
    except Exception as e:
        print("Erreur dans RecuperTous:", e)
    return data

def recuperer_pages_totales(driver, url):
    driver.get(url)
    time.sleep(2)

    max_page = 1
    visited = set()

    try:
        while True:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="pagination-item"]'))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            pagination_buttons = soup.select('[data-test-id="pagination-item"]')

            for btn in pagination_buttons:
                try:
                    page_num = int(btn.text.strip())
                    visited.add(page_num)
                except ValueError:
                    continue

            # Cherche le bouton ">" (pagination suivante)
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, '[data-spark-component="pagination-next-trigger"]')
                if "cursor-not-allowed" in next_btn.get_attribute("class"):
                    break  # Si le bouton est désactivé, on arrête
                else:
                    next_btn.click()
                    time.sleep(1.5)  # laisser le temps à la page de recharger
            except Exception:
                break  # pas de bouton ">", fin

    except Exception as e:
        print("❌ Erreur pagination dynamique :", e)

    if visited:
        max_page = max(visited)
    return max_page


def envoyer_mail(fichier, destinataire):
    try:
        yag = yagmail.SMTP("ainabruno56@gmail.com", "wyrj xcsd ycko ptgy")
        sujet = "Annonces immobilières Leboncoin du jour"
        corps = "Voici les nouvelles annonces récupérées automatiquement aujourd'hui."
        
        # Ouvrir le fichier en mode binaire pour éviter problème d'encodage
        with open(fichier, "rb") as f:
            contenu = f.read()

        # Envoyer le mail avec la pièce jointe en bytes
        yag.send(
            to=destinataire,
            subject=sujet,
            contents=corps,
            attachments=[(fichier, contenu)]
        )
        print("📩 Mail envoyé avec succès à", destinataire)
    except Exception as e:
        print("Erreur lors de l'envoi de l'e-mail:", e)

def main(ville, type_bien, pieces_min, budget_max, destinataire_email):
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(options=options, use_subprocess=True)

    base_url = "https://www.leboncoin.fr/recherche"
    resultats = []
    toutes_urls = set()

    nom_fichier = f"annonces_{ville.lower()}_{type_bien}_{budget_max}eu.csv"
    if os.path.exists(nom_fichier):
        df_old = pd.read_csv(nom_fichier)
        toutes_urls = set(df_old["url"].values)
        resultats.extend(df_old.to_dict("records"))

    url_page1 = construire_url(base_url, ville, type_bien, budget_max, pieces_min, page=1)
    nb_pages = recuperer_pages_totales(driver, url_page1)

    print(f"🔁 Nombre de pages détectées : {nb_pages}")

    for i in range(1, nb_pages + 1):
        url = construire_url(base_url, ville, type_bien, budget_max, pieces_min, page=i)
        print(f"🔗 Page {i}: {url}")
        driver.get(url)
        time.sleep(random.uniform(1, 2))
        urls = RecuperUrl(driver)
        print(f"➡️ {len(urls)} annonces trouvées")

        for annonce_url in urls:
            if annonce_url in toutes_urls:
                continue
            print(f"🔍 Nouvelle annonce: {annonce_url}")
            infos = RecuperTous(annonce_url, driver)
            toutes_urls.add(annonce_url)
            resultats.append(infos)

    driver.quit()
    pd.DataFrame(resultats).to_csv(nom_fichier, index=False, encoding="utf-8")
    print(f"✅ Export terminé dans '{nom_fichier}'")

    if destinataire_email:
        envoyer_mail(nom_fichier, destinataire_email)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Leboncoin avec filtres dynamiques et historique.")
    parser.add_argument("--ville", default="Toulouse")
    parser.add_argument("--type_bien", default="2", help="1: maison, 2: appartement")
    parser.add_argument("--pieces_min", type=int, default=3)
    parser.add_argument("--budget_max", type=int, default=150000)
    parser.add_argument("--destinataire", type=str, help="Adresse e-mail du destinataire")
    args = parser.parse_args()

    main(args.ville, args.type_bien, args.pieces_min, args.budget_max, args.destinataire)
