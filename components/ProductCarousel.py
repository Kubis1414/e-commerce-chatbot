import streamlit as st

def product_carousel(products):
    """
    Zobrazí mřížku s doporučenými produkty - reaguje na Light/Dark mód.
    - Karty mají konzistentní výšku obrázkové části.
    - Popis je omezen s tooltipem.
    - Celá karta je klikatelná (pokud produkt má URL).
    - Barvy se přizpůsobují Streamlit tématu (Light/Dark).

    Args:
        products (list): Seznam slovníků produktů k zobrazení.
                         Každý slovník by měl obsahovat klíče:
                         'name', 'url', 'image_url', 'description', 'price'.
    """
    if not products:
        st.write("Žádné doporučené produkty k zobrazení.")
        return

    # --- 1. Definice CSS Stylů s Theme Proměnnými ---
    # Tyto styly používají CSS proměnné Streamlitu (--text-color, --secondary-background-color atd.)
    # aby se přizpůsobily světlému i tmavému režimu.
    st.markdown("""
    <style>
    /* --- Kontejner pro celou kartu --- */
    .product-card-container {{
        height: 100%;
        display: flex;
        flex-direction: column;
        /* Použijeme proměnnou pro barvu pozadí karty */
        background-color: var(--secondary-background-color);
         /* Rámeček odvozený od barvy textu s nízkou průhledností */
        border: 1px solid rgba(var(--text-color-rgb), 0.1);
        border-radius: 8px;
        margin-bottom: 15px;
        overflow: hidden;
    }}

    /* --- Odkaz obalující celou kartu (nebo fallback div) --- */
    a.product-card-link, div.product-card-link {{
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        text-decoration: none;
        /* Explicitně nastavíme barvu textu tématu */
        color: var(--text-color);
        padding: 10px;
        transition: box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
    }}

    /* --- Hover efekt pro odkaz --- */
    a.product-card-link:hover {{
         /* Mírně tmavší/světlejší pozadí při najetí */
        background-color: rgba(var(--text-color-rgb), 0.03);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Stín může zůstat jemný */
        color: var(--text-color); /* Barva textu se nemění */
        text-decoration: none;
    }}

    /* --- Kontejner pro obrázek --- */
    .product-image-container {{
        height: 200px; /* Pevná výška */
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 15px;
    }}

    /* --- Samotný obrázek --- */
    .product-image {{
        max-height: 100%;
        max-width: 100%;
        object-fit: contain;
        border-radius: 4px;
    }}

    /* --- Kontejner pro textovou část --- */
    .product-details {{
         flex-grow: 1;
         display: flex;
         flex-direction: column;
    }}
    .product-details h5 {{ /* Název produktu */
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 1em;
        font-weight: 600;
        /* Použijeme barvu textu tématu */
        color: var(--text-color);
        /* Omezení na 2 řádky s tečkami */
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
        min-height: 2.6em;
    }}
    .product-details small {{ /* Popis produktu */
        font-size: 0.85em;
        /* Použijeme barvu textu tématu, ale méně výraznou (nižší opacita) */
        color: var(--text-color);
        opacity: 0.7;
        line-height: 1.4;
        margin-bottom: 10px;
        /* Omezení na 3 řádky s tečkami */
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        min-height: 4.2em;
    }}

    /* --- Kontejner pro cenu --- */
    .product-price {{
        margin-top: auto;
        padding-top: 10px;
        font-size: 1.1em;
        font-weight: bold;
        text-align: right;
        /* Použijeme barvu textu tématu */
        color: var(--text-color);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 2. Zobrazení produktů s použitím CSS tříd ---
    num_columns = min(len(products), 4) # Max 4 sloupce
    cols = st.columns(num_columns)

    for idx, product in enumerate(products):
        col_index = idx % num_columns
        with cols[col_index]:
            # Získání dat (s výchozími hodnotami pro bezpečnost)
            name = product.get('name', 'Neznámý produkt')
            url = product.get('url')
            image_url = product.get('image_url') # Získáme hodnotu
            # Kontrola, zda image_url je None, prázdný string nebo jen bílé znaky
            if not image_url or not str(image_url).strip():
                image_url = "https://placehold.co/400x300?text=Obrázek+není+k+dispozici" # Placeholder

            full_description = product.get("description", "")
            price = product.get("price")

            # Omezení popisku pro zobrazení
            max_desc_length = 70 # Limit pro popis
            ellipsis = "..."
            display_description = full_description # Výchozí hodnota
            tooltip_text = None # Tooltip jen pokud zkracujeme

            if len(full_description) > max_desc_length:
                chars_to_keep = max_desc_length - len(ellipsis)
                if chars_to_keep > 0:
                   display_description = full_description[:chars_to_keep] + ellipsis
                   tooltip_text = full_description # Plný text do tooltipu
                else: # Pokud limit < délka elipsy
                   display_description = full_description[:max_desc_length]
                   tooltip_text = full_description

            # Formátování ceny
            if price is not None:
                # Formátování na celé koruny s nezlomitelnou mezerou
                formatted_price = f"{price:,.0f} Kč".replace(",", " ")
            else:
                formatted_price = "Cena neuvedena"

            # Sestavení HTML karty
            # Pokud URL existuje, obalíme kartu odkazem <a>, jinak použijeme <div>
            link_start = f'<a href="{url}" target="_blank" class="product-card-link" title="Zobrazit detail produktu: {name}">' if url else '<div class="product-card-link">'
            link_end = '</a>' if url else '</div>'

            # HTML struktura karty
            card_html = f"""
            <div class="product-card-container">
                {link_start}
                    <div class="product-image-container">
                        <img src="{image_url}" class="product-image" alt="{name}" loading="lazy">
                    </div>
                    <div class="product-details">
                        <h5>{name}</h5>
                        <small {'title="'+tooltip_text+'"' if tooltip_text else ''}>{display_description if display_description else ' '}</small>
                        <div class="product-price">
                            {formatted_price}
                        </div>
                    </div>
                {link_end}
            </div>
            """
            # Vykreslení karty pomocí Streamlit markdown
            st.markdown(card_html, unsafe_allow_html=True)