import streamlit as st
from datetime import datetime, date
import json
import base64
import os
from streamlit_sortables import sort_items
import hashlib

st.set_page_config(page_title="Deepfocus Kanban", layout="wide")

@st.cache_data
def get_video_base64(video_file):
    """Encode la vidéo une seule fois pour optimiser les performances."""
    if os.path.exists(video_file):
        with open(video_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def add_bg_video(video_file):
    bin_str = get_video_base64(video_file)
    if bin_str:
        st.markdown(
            f"""
            <style>
            /* Vidéo de fond */
            #myVideo {{
                position: fixed; right: 0; bottom: 0;
                min-width: 100%; min-height: 100%;
                z-index: -1; object-fit: cover;
                filter: brightness(0.5) saturate(1.2);
            }}
            .stApp {{ background: transparent !important; }}
            [data-testid="stAppViewContainer"] {{
                background: transparent !important;
            }}
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}

            /* Conteneur Liquid Glass spécifique pour Login */
            .glass-card {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(25px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
                margin-top: 50px;
            }}

            /* Titres en Néon Gradient */
            h1, h2, h3, .neon-text {{
                background: linear-gradient(45deg, #00f2fe 0%, #4facfe 50%, #f093fb 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800 !important;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            /* Effet Liquid Glass pour les inputs et containers */
            div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {{
                background: rgba(255, 255, 255, 0.05) !important;
                backdrop-filter: blur(15px) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 10px !important;
                color: white !important;
            }}

            /* Style des Placeholders */
            ::placeholder {{
                color: rgba(255, 255, 255, 0.4) !important;
                font-style: italic;
            }}
            
            /* Styling des onglets (Tabs) */
            .stTabs [data-baseweb="tab-list"] {{
                background-color: transparent !important;
            }}

            /* Sidebar Glassmorphism */
            [data-testid="stSidebar"] {{
                background: rgba(0, 0, 0, 0.3) !important;
                backdrop-filter: blur(20px);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}

            /* Boutons */
            .stButton>button {{
                background: linear-gradient(45deg, rgba(79, 172, 254, 0.5), rgba(0, 242, 254, 0.5)) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                color: white !important;
                backdrop-filter: blur(5px);
                transition: 0.3s;
            }}
            .stButton>button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 242, 254, 0.4);
            }}
            </style>
            <video autoplay muted loop playsinline id="myVideo">
                <source src="data:video/mp4;base64,{bin_str}" type="video/mp4">
            </video>
            """,
            unsafe_allow_html=True
        )

add_bg_video("1.mp4")

# --- State initialization --------------------------------------------------
def init_state():
    defaults = {
        "boards": [{"id": 1, "name": "Tableau Deepfocus", "lists": [
            {"id": 1, "name": "À faire", "cards": []},
            {"id": 2, "name": "En cours", "cards": []},
            {"id": 3, "name": "Terminé", "cards": []}
        ]}],
        "selected_board_id": 1,
        "next_board_id": 2,
        "next_list_id": 4,
        "next_card_id": 1,
        "selected_card_id": None,
        "show_archived": False,
        "card_filter": "",
        "logged_in": False,
        "current_user": None,
        "users": {}, # Format: {username: password}
        "editing_list_id": None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

def hash_password(password):
    """Hache le mot de passe pour une sécurité basique."""
    return hashlib.sha256(password.encode()).hexdigest()

def render_login_page():
    st.markdown('<div class="neon-text" style="text-align:center; font-size:4rem; margin-top:50px;">DEEPFOCUS</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; color:white; opacity:0.7; letter-spacing:2px;">K A N B A N  ·  S Y S T E M</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["Se connecter", "S'inscrire"])
        
        with tab_login:
            user_in = st.text_input("Nom d'utilisateur", key="login_user")
            pass_in = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.button("Connexion", use_container_width=True):
                if user_in in st.session_state.users and st.session_state.users[user_in] == hash_password(pass_in):
                    st.session_state.logged_in = True
                    st.session_state.current_user = user_in
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        
        with tab_signup:
            new_user = st.text_input("Choisir un pseudo", key="sig_user")
            new_pass = st.text_input("Choisir un mot de passe", type="password", key="sig_pass")
            confirm_pass = st.text_input("Confirmer le mot de passe", type="password")
            if st.button("Créer un compte", use_container_width=True):
                if not new_user or not new_pass:
                    st.warning("Veuillez remplir tous les champs")
                elif new_pass != confirm_pass:
                    st.error("Les mots de passe ne correspondent pas")
                elif new_user in st.session_state.users:
                    st.error("Cet utilisateur existe déjà")
                else:
                    st.session_state.users[new_user] = hash_password(new_pass)
                    st.success("Compte créé ! Connectez-vous.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Helper functions ------------------------------------------------------
def get_selected_board():
    return next((board for board in st.session_state.boards if board["id"] == st.session_state.selected_board_id), st.session_state.boards[0])


def get_list(board, list_id):
    return next((lst for lst in board["lists"] if lst["id"] == list_id), None)


def get_card(board, card_id):
    for lst in board["lists"]:
        card = next((card for card in lst["cards"] if card["id"] == card_id), None)
        if card:
            return lst, card
    return None, None


def add_board(name):
    st.session_state.boards.append({"id": st.session_state.next_board_id, "name": name, "lists": []})
    st.session_state.selected_board_id = st.session_state.next_board_id
    st.session_state.next_board_id += 1


def add_list(board, name):
    board["lists"].append({"id": st.session_state.next_list_id, "name": name, "cards": []})
    st.session_state.next_list_id += 1


def add_card(board, list_id, title, description, label, due_date, members, checklist, attachments):
    lst = get_list(board, list_id)
    if not lst:
        return
    card = {
        "id": st.session_state.next_card_id,
        "title": title,
        "description": description,
        "label": label,
        "due_date": due_date.isoformat() if due_date else "",
        "members": [member.strip() for member in members.split(",") if member.strip()],
        "checklist": [{"text": item, "done": False} for item in checklist.splitlines() if item.strip()],
        "comments": [],
        "attachments": attachments,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "archived": False,
    }
    lst["cards"].append(card)
    st.session_state.next_card_id += 1


def update_card(board, card_id, title, description, label, due_date, members, checklist, attachments, list_id):
    lst, card = get_card(board, card_id)
    if not card:
        return
    card.update(
        {
            "title": title,
            "description": description,
            "label": label,
            "due_date": due_date.isoformat() if due_date else "",
            "members": [member.strip() for member in members.split(",") if member.strip()],
            "checklist": [{"text": item.replace("[x]", "").replace("[X]", "").strip(), "done": item.lower().startswith("[x]")} for item in checklist.splitlines() if item.strip()],
            "attachments": attachments,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    if lst["id"] != list_id:
        new_list = get_list(board, list_id)
        if new_list:
            lst["cards"].remove(card)
            new_list["cards"].append(card)


def delete_card(board, card_id):
    for lst in board["lists"]:
        lst["cards"] = [card for card in lst["cards"] if card["id"] != card_id]


def archive_card(board, card_id):
    _, card = get_card(board, card_id)
    if card:
        card["archived"] = True


def restore_card(board, card_id):
    _, card = get_card(board, card_id)
    if card:
        card["archived"] = False


def copy_card(board, card_id):
    lst, card = get_card(board, card_id)
    if card and lst:
        copy = card.copy()
        copy["id"] = st.session_state.next_card_id
        copy["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        copy["updated_at"] = copy["created_at"]
        copy["comments"] = []
        copy["archived"] = False
        st.session_state.next_card_id += 1
        lst["cards"].append(copy)


def move_card(board, card_id, direction):
    lst, card = get_card(board, card_id)
    if not card or not lst:
        return
    board_lists = board["lists"]
    idx = next((i for i, value in enumerate(board_lists) if value["id"] == lst["id"]), None)
    if idx is None:
        return
    new_idx = max(0, min(len(board_lists) - 1, idx + direction))
    if new_idx != idx:
        board_lists[idx]["cards"] = [c for c in board_lists[idx]["cards"] if c["id"] != card_id]
        board_lists[new_idx]["cards"].append(card)


def add_comment(board, card_id, comment_text):
    _, card = get_card(board, card_id)
    if card and comment_text.strip():
        card["comments"].append(
            {
                "text": comment_text.strip(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        card["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def toggle_checklist_item(board, card_id, item_index):
    _, card = get_card(board, card_id)
    if card and 0 <= item_index < len(card["checklist"]):
        card["checklist"][item_index]["done"] = not card["checklist"][item_index]["done"]
        card["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_label(label):
    return f"#{label}" if label else ""


def upload_attachments(files):
    attachments = []
    for file in files:
        attachments.append(
            {
                "name": file.name,
                "type": file.type,
                "size": file.size,
                "data": file.getvalue(),
            }
        )
    return attachments


def filter_card(card):
    if not st.session_state.card_filter:
        return True
    query = st.session_state.card_filter.lower()
    return query in card["title"].lower() or query in card["description"].lower() or any(query in comment["text"].lower() for comment in card["comments"])


def render_card_preview(card):
    badge = f"<span style='background:#{card['label']};color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.75rem;'> {format_label(card['label'])} </span>" if card["label"] else ""
    due = f"<div style='font-size:0.8rem;color:#ddd;'>📅 {card['due_date']}</div>" if card["due_date"] else ""
    members = f"<div style='font-size:0.8rem;color:#ddd;'>👥 {', '.join(card['members'])}</div>" if card["members"] else ""
    checklist = "✅ {}".format(sum(1 for item in card["checklist"] if item["done"])) + f" / {len(card['checklist'])}" if card["checklist"] else ""
    checklist_line = f"<div style='font-size:0.8rem;color:#ddd;'>{checklist}</div>" if checklist else ""
    archived = "<div style='font-size:0.75rem;color:#a00;'>Archivée</div>" if card["archived"] else ""
    st.markdown(
        f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));"
        f"backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.15); border-radius: 1rem; "
        f"padding: 1rem; margin-bottom: 0.9rem; color: white; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
        f"<strong style='font-size:1.1rem; letter-spacing:0.5px;'>{card['title']}</strong>{badge}"
        f"</div>"
        f"<div style='margin-top:0.5rem;color:#eee;font-size:0.9rem;'>{card['description'][:100]}{'...' if len(card['description']) > 100 else ''}</div>"
        f"{due}{members}{checklist_line}{archived}"
        f"</div>", unsafe_allow_html=True,
    )

def serialize_board(board):
    """Sérialise le tableau en JSON en excluant les données binaires des pièces jointes."""
    export_data = {"id": board["id"], "name": board["name"], "lists": []}
    for lst in board["lists"]:
        new_list = {"id": lst["id"], "name": lst["name"], "cards": []}
        for card in lst["cards"]:
            card_copy = card.copy()
            # On ne garde que les métadonnées des pièces jointes (pas les bytes)
            card_copy["attachments"] = [
                {"name": a["name"], "type": a["type"], "size": a["size"]}
                for a in card.get("attachments", [])
            ]
            new_list["cards"].append(card_copy)
        export_data["lists"].append(new_list)
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def render_attachments(card):
    if not card.get("attachments"):
        return
    st.markdown("**Pièces jointes :**")
    for idx, attach in enumerate(card["attachments"]):
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"- {attach['name']} ({attach['type'] or 'inconnu'}, {attach['size']} octets)")
        with cols[1]:
            st.download_button(
                label="Télécharger",
                data=attach["data"],
                file_name=attach["name"],
                mime=attach["type"] or "application/octet-stream",
                key=f"download_{card['id']}_{idx}",
            )


def update_lists_from_dnd(board, sorted_containers):
    if not isinstance(sorted_containers, list):
        return
    target_card_map = {card['id']: card for lst in board['lists'] for card in lst['cards']}
    new_lists = []
    for container in sorted_containers:
        header = container.get('header')
        items = container.get('items', [])
        lst = next((lst for lst in board['lists'] if lst['name'] == header), None)
        if not lst:
            continue
        new_cards = []
        for item_str in items:
            card_id = int(item_str.split('||', 1)[0])
            if card_id in target_card_map:
                new_cards.append(target_card_map[card_id])
        lst['cards'] = new_cards
        new_lists.append(lst)
    board['lists'] = new_lists


# --- Main Application Flow --------------------------------------------------
if not st.session_state.logged_in:
    render_login_page()
    st.stop()


# --- UI ---------------------------------------------------------------------
board = get_selected_board()
st.title("Deepfocus — Tableau Kanban style Deep Tech")
st.markdown("Gestion multi-listes, cartes, commentaires, checklists, étiquettes, pièces jointes et archives.")

with st.expander("Glisser-déposer les cartes", expanded=True):
    dnd_items = [
        {
            "header": lst["name"],
            "items": [f"{card['id']}||{card['title']}" for card in lst["cards"] if (st.session_state.show_archived or not card["archived"])],
        }
        for lst in board["lists"]
    ]
    sorted_containers = sort_items(
        dnd_items,
        multi_containers=True,
        direction="horizontal",
        custom_style=".sortable-item {padding:0.6rem;margin:0.3rem 0;border-radius:0.8rem;background:rgba(255,255,255,0.1); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.1); color:white;} .sortable-container {background:rgba(0,0,0,0.2);border-radius:0.9rem;padding:0.5rem; border:1px solid rgba(255,255,255,0.05);}",
        key="board_dnd",
    )
    if sorted_containers and sorted_containers != dnd_items:
        update_lists_from_dnd(board, sorted_containers)
        st.success("Ordre des cartes mis à jour.")
        st.rerun()

with st.sidebar:
    st.markdown(f'<div class="neon-text" style="font-size:1.5rem; margin-bottom:10px;">Salut, {st.session_state.current_user}</div>', unsafe_allow_html=True)
    
    c_auth1, c_auth2 = st.columns(2)
    with c_auth1:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    with c_auth2:
        if st.button("Suppression", use_container_width=True):
            user = st.session_state.current_user
            if user in st.session_state.users:
                del st.session_state.users[user]
            st.session_state.clear() # Wipes all boards and session data
            st.rerun()

    st.markdown("---")
    st.header("Tableaux")
    board_options = {b["id"]: b["name"] for b in st.session_state.boards}
    current_board_idx = next((i for i, b in enumerate(st.session_state.boards) if b["id"] == st.session_state.selected_board_id), 0)
    
    selected_id = st.selectbox(
        "Sélectionner un tableau",
        options=list(board_options.keys()),
        format_func=lambda x: board_options[x],
        index=current_board_idx
    )
    if selected_id != st.session_state.selected_board_id:
        st.session_state.selected_board_id = selected_id
        st.rerun()

    board = get_selected_board()

    with st.expander("Créer / renommer un tableau", expanded=True):
        new_board_name = st.text_input("Nouveau nom de tableau")
        if st.button("Ajouter un tableau") and new_board_name.strip():
            add_board(new_board_name.strip())
            st.rerun()

        rename_board_name = st.text_input("Renommer ce tableau", value=board["name"])
        if st.button("Renommer le tableau") and rename_board_name.strip():
            board["name"] = rename_board_name.strip()
            st.rerun()

    st.markdown("---")
    st.header("Listes")
    list_name = st.text_input("Nouvelle liste")
    if st.button("Ajouter une liste") and list_name.strip():
        add_list(board, list_name.strip())
        st.rerun()

    st.markdown("---")
    st.header("Filtrer / afficher")
    st.session_state.card_filter = st.text_input("Rechercher dans les cartes", value=st.session_state.card_filter)
    st.session_state.show_archived = st.checkbox("Afficher archivées", value=st.session_state.show_archived)

    st.markdown("---")
    st.header("Ajouter une carte")
    if board["lists"]:
        with st.form(key="new_card_form"):
            card_title = st.text_input("Titre de la carte", max_chars=80)
            card_description = st.text_area("Description", max_chars=300)
            target_list_name = st.selectbox("Liste", [lst["name"] for lst in board["lists"]])
            target_list = next(lst for lst in board["lists"] if lst["name"] == target_list_name)
            card_label = st.color_picker("Couleur de l'étiquette", value="#007bff").lstrip("#")
            card_due_date = st.date_input("Échéance", value=date.today())
            card_members = st.text_input("Membres (séparés par virgule)")
            card_checklist = st.text_area("Checklist (une ligne par élément)")
            card_files = st.file_uploader("Fichiers", accept_multiple_files=True, type=None)
            card_attachments = upload_attachments(card_files) if card_files else []
            submitted = st.form_submit_button("Créer la carte")
            if submitted:
                if not card_title.strip():
                    st.warning("Le titre est requis.")
                else:
                    add_card(
                        board,
                        target_list["id"],
                        card_title.strip(),
                        card_description.strip(),
                        card_label or "007bff",
                        card_due_date,
                        card_members,
                        card_checklist,
                        card_attachments,
                    )
                    st.success("Carte créée !")
                    st.rerun()
    else:
        st.info("Ajoutez d'abord une liste pour créer une carte.")

    st.markdown("---")
    st.header("Export")
    st.download_button("Exporter le tableau JSON", serialize_board(board), file_name=f"tableau_{board['name']}.json", mime="application/json")
    if st.button("Réinitialiser ce tableau"):
        for lst in board["lists"]:
            lst["cards"] = []
        st.session_state.selected_card_id = None
        st.rerun()


# --- Board layout -----------------------------------------------------------
lists = board["lists"]
if not lists:
    st.warning("Ajoutez une liste pour commencer.")
else:
    columns = st.columns(max(1, len(lists)))
    for idx, lst in enumerate(lists):
        with columns[idx]:
            st.subheader(lst["name"])
            
            # Zone de gestion de la liste
            if st.session_state.editing_list_id == lst["id"]:
                new_lst_name = st.text_input("Nom de la liste", value=lst["name"], key=f"input_ren_{lst['id']}", label_visibility="collapsed")
                c_edit1, c_edit2 = st.columns(2)
                if c_edit1.button("✅", key=f"save_lst_{lst['id']}", use_container_width=True):
                    if new_lst_name.strip():
                        lst["name"] = new_lst_name.strip()
                    st.session_state.editing_list_id = None
                    st.rerun()
                if c_edit2.button("❌", key=f"cancel_lst_{lst['id']}", use_container_width=True):
                    st.session_state.editing_list_id = None
                    st.rerun()
            else:
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("Renommer", key=f"ren_btn_{lst['id']}", use_container_width=True):
                    st.session_state.editing_list_id = lst["id"]
                    st.rerun()
                if c_btn2.button("Supprimer", key=f"del_btn_{lst['id']}", use_container_width=True):
                    board["lists"] = [l for l in board["lists"] if l["id"] != lst["id"]]
                    st.rerun()

            visible_cards = [card for card in lst["cards"] if (st.session_state.show_archived or not card["archived"]) and filter_card(card)]
            if not visible_cards:
                st.info("Aucune carte.")

            for card in visible_cards:
                with st.expander(card["title"], expanded=False):
                    render_card_preview(card)
                    st.markdown(f"**Description:** {card['description'] if card['description'] else '_Aucune description_'}")
                    st.markdown(f"**Créée le :** {card['created_at']}")
                    if card["due_date"]:
                        st.markdown(f"**Échéance :** {card['due_date']}")
                    if card["members"]:
                        st.markdown(f"**Membres :** {', '.join(card['members'])}")
                    if card["checklist"]:
                        checklist_text = ' '.join([f"[{ 'x' if item['done'] else ' ' }] {item['text']}" for item in card['checklist']])
                        st.markdown(f"**Checklist :** {checklist_text}")
                    if card["comments"]:
                        st.markdown(f"**Commentaires :** {len(card['comments'])}")
                    row1, row2, row3 = st.columns(3)
                    with row1:
                        if st.button("←", key=f"move_left_{card['id']}"):
                            move_card(board, card["id"], -1)
                            st.rerun()
                    with row2:
                        if st.button("→", key=f"move_right_{card['id']}"):
                            move_card(board, card["id"], 1)
                            st.rerun()
                    with row3:
                        if st.button("Ouvrir", key=f"open_{card['id']}"):
                            st.session_state.selected_card_id = card["id"]
                    row4, row5, row6 = st.columns(3)
                    with row4:
                        if st.button("Archiver", key=f"archive_{card['id']}"):
                            archive_card(board, card["id"])
                            st.rerun()
                    with row5:
                        if st.button("Copier", key=f"copy_{card['id']}"):
                            copy_card(board, card["id"])
                            st.rerun()
                    with row6:
                        if st.button("Supprimer", key=f"delete_{card['id']}"):
                            delete_card(board, card["id"])
                            if st.session_state.selected_card_id == card["id"]:
                                st.session_state.selected_card_id = None
                            st.rerun()


# --- Selected card details --------------------------------------------------
if st.session_state.selected_card_id is not None:
    lst, selected_card = get_card(board, st.session_state.selected_card_id)
    if selected_card:
        st.markdown("---")
        st.header(f"Détails de la carte : {selected_card['title']}")
        with st.form(key="edit_card_form"):
            title = st.text_input("Titre", value=selected_card["title"])
            description = st.text_area("Description", value=selected_card["description"])
            status_choice = st.selectbox("Liste", [lst_obj["name"] for lst_obj in board["lists"]], index=[i for i, l in enumerate(board["lists"]) if l["id"] == lst["id"]][0])
            list_id = [lst_obj["id"] for lst_obj in board["lists"] if lst_obj["name"] == status_choice][0]
            label = st.color_picker("Couleur de l'étiquette", value=f"#{selected_card['label']}" if selected_card["label"] else "#007bff").lstrip("#")
            due_date = st.date_input("Échéance", value=date.fromisoformat(selected_card["due_date"]) if selected_card["due_date"] else date.today())
            members = st.text_input("Membres", value=",".join(selected_card["members"]))
            checklist_items = st.text_area(
                "Checklist (ajoutez [x] pour marquer fait)",
                value="\n".join([f"[x] {item['text']}" if item['done'] else item['text'] for item in selected_card["checklist"]]),
            )
            if selected_card.get("attachments"):
                st.markdown("**Pièces jointes existantes :**")
                for idx, attach in enumerate(selected_card["attachments"]):
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.write(f"{attach['name']} ({attach['type'] or 'inconnu'})")
                    with cols[1]:
                        if st.button("Supprimer", key=f"remove_attach_{selected_card['id']}_{idx}"):
                            selected_card["attachments"].pop(idx)
                            st.rerun()
            new_files = st.file_uploader("Ajouter des fichiers", accept_multiple_files=True, type=None)
            comment_text = st.text_area("Ajouter un commentaire")
            submitted = st.form_submit_button("Enregistrer les modifications")
            if submitted:
                if not title.strip():
                    st.warning("Le titre ne peut pas être vide.")
                else:
                    update_card(
                        board,
                        selected_card["id"],
                        title.strip(),
                        description.strip(),
                        label.strip() or "007bff",
                        due_date,
                        members,
                        checklist_items,
                        selected_card.get("attachments", []) + (upload_attachments(new_files) if new_files else []),
                        list_id,
                    )
                    if comment_text.strip():
                        add_comment(board, selected_card["id"], comment_text)
                    st.success("Carte mise à jour !")
                    st.rerun()

        if selected_card["comments"]:
            st.subheader("Commentaires")
            for comment in selected_card["comments"]:
                st.markdown(f"- {comment['text']} <span style='color:#555;font-size:0.85rem;'>({comment['created_at']})</span>", unsafe_allow_html=True)
    else:
        st.session_state.selected_card_id = None
