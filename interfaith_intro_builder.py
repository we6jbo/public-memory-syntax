#!/usr/bin/env python3
"""
Interfaith Intro Builder for membership13

Creates a local Tkinter question app that helps Jeremiah O'Neal draft a forum intro.
Answers are stored in: /home/we6jbo/.interfaith/
PII is stored/read from: /home/we6jbo/.restore-interfaith-pii/
Restore button downloads public non-PII files from:
https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/
"""

import json
import os
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

PROJECT = "membership13"
BASE_DIR = Path.home() / ".interfaith"
PII_DIR = Path.home() / ".restore-interfaith-pii"
CONFIG_FILE = BASE_DIR / "interfaith_intro_config.json"
ANSWERS_FILE = BASE_DIR / "interfaith_intro_answers.json"
SUMMARY_FILE = BASE_DIR / "interfaith_intro_forum_post.txt"
RESEARCH_FILE = BASE_DIR / "interfaith_research_notes.json"
PII_FILE = PII_DIR / "jeremiah_private_profile.json"
BACKUP_DIR = BASE_DIR / "backups"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/we6jbo/public-memory-syntax/refs/heads/main/"
RESTORE_FILENAMES = [
    "interfaith_intro_builder.py",
    "interfaith_intro_config.json",
    "interfaith_questions.json",
    "interfaith_sources.json",
]

DEFAULT_CONFIG = {
    "project": PROJECT,
    "created_by": "ChatGPT",
    "purpose": "Build a careful forum intro for an interfaith/science/religion discussion board.",
    "storage_dir": str(BASE_DIR),
    "pii_dir": str(PII_DIR),
    "answer_file": str(ANSWERS_FILE),
    "summary_file": str(SUMMARY_FILE),
    "research_file": str(RESEARCH_FILE),
    "github_raw_base": GITHUB_RAW_BASE,
    "restore_files": RESTORE_FILENAMES,
    "privacy_note": "Public intro should avoid phone numbers, street addresses, full DOB, medical details, or family details unless Jeremiah chooses to include them.",
}

DEFAULT_PII = {
    "legal_name": "Jeremiah Burke O'Neal",
    "forum_handle": "we6jbo",
    "birth_date": "1981-03-24",
    "birth_city": "San Diego, California",
    "baptism": {
        "date": "1983-01-12",
        "church": "Holy Cross Lutheran Church",
        "church_address_on_certificate": "3450 Clairemont Dr.",
        "pastor": "The Rev. Edward W. Wessling",
        "sponsors": ["Robert Maynard", "Betty Maynard"],
        "certificate_claim": "By Baptism God has made you a member of the holy Christian church."
    },
    "education": {
        "bachelors": "B.S. Information Technology Management, National University",
        "masters": "M.S. Cybersecurity, National University, November 2023"
    },
    "work_public": {
        "role": "Network Systems Technician",
        "district_context": "San Diego Unified School District / Rosa Parks Elementary public technology-support context"
    },
    "medical_private_summary": "Childhood speech/language delay and learning-disability history. Keep this private unless Jeremiah chooses otherwise.",
    "book": "Sufficiently Educated: From struggling to a college degree",
    "bbs_history": "Quendor BBS, Pacific Beach, San Diego area, 1998-2000",
    "genealogy_public_path": "Jeremiah O'Neal -> Doug O'Neal -> Noma Vade Smith -> Archie T. Smith -> Rose Ann Prickett -> Adaline A. Holderman -> Jakob Holderman Sr.",
}

RESEARCH_NOTES = {
    "publicly_found_online": [
        {
            "claim": "Sufficiently Educated is publicly described as chronicling O'Neal's struggles with the U.S. educational system and overcoming learning disabilities toward educational and occupational goals.",
            "source": "sufficientlyeducated.com"
        },
        {
            "claim": "ResearchGate lists Sufficiently Educated Book with author Jeremiah O'Neal, publisher Jeremiah O'Neal, ISBN 978-0578755601, and DOI 10.5281/zenodo.7783660.",
            "source": "ResearchGate / Zenodo metadata"
        },
        {
            "claim": "A public Reddit/BBS listing describes Quendor BBS in Pacific Beach, CA, 1998-2000, with SYSOP Jeremiah O'Neal.",
            "source": "reddit.com/r/bbs and bbslist.textfiles.com/619/"
        },
        {
            "claim": "A public Rosa Parks Elementary tech support page references Jeremiah O'Neal in a school technology-support context.",
            "source": "rosaparks.sandiegounified.org"
        },
        {
            "claim": "LinkedIn search results identify Jeremiah O'Neal / we6jbo as a Network Systems Technician at Rosa Parks Elementary and describe long-term hands-on educational IT experience.",
            "source": "LinkedIn search result snippet"
        }
    ],
    "user_provided_verified_by_user": [
        "Certificate of Baptism images and wording supplied by Jeremiah.",
        "Private pediatric neurology document image supplied by Jeremiah.",
        "Forum thread screenshot showing Thomas invited @we6bjo to post on the Intro board.",
        "Screenshots of Sufficiently Educated pages, LinkedIn, Rosa Parks page, BBS post, science/religion videos, and genealogy notes supplied by Jeremiah."
    ],
    "intro_strategy": "Answer the forum invitation with a friendly, non-combative introduction: San Diego, lifelong technology learner, education and cybersecurity background, author/personal learning history, baptized Lutheran background, current science-first/atheist understanding, curiosity about religion, evolution, ritual, and belonging."
}

QUESTIONS = [
    {"id":"q01", "type":"text", "label":"What name do you want to use in the intro?", "default":"Jeremiah"},
    {"id":"q02", "type":"text", "label":"What forum handle should the intro mention?", "default":"we6jbo"},
    {"id":"q03", "type":"dropdown", "label":"How much personal detail should the public intro include?", "options":["Very short", "Moderate", "Detailed but safe", "Full personal story"], "default":"Detailed but safe"},
    {"id":"q04", "type":"yesno", "label":"Mention San Diego?", "default":True},
    {"id":"q05", "type":"yesno", "label":"Mention being born in San Diego?", "default":False},
    {"id":"q06", "type":"yesno", "label":"Mention the full birth date? Usually keep private.", "default":False},
    {"id":"q07", "type":"text", "label":"What one sentence describes why you joined the forum?", "default":"I joined because I want to learn from deep discussions about religion, science, belief, and human meaning."},
    {"id":"q08", "type":"dropdown", "label":"Current belief wording", "options":["atheist", "science-first", "atheist but interested in religion", "still deciding how to describe it"], "default":"atheist but interested in religion"},
    {"id":"q09", "type":"yesno", "label":"Mention that you are careful with the word theory?", "default":True},
    {"id":"q10", "type":"dropdown", "label":"Tone for science and religion", "options":["Respectful", "Curious", "Personal", "Academic"], "default":"Curious"},
    {"id":"q11", "type":"yesno", "label":"Mention your baptism certificate?", "default":True},
    {"id":"q12", "type":"yesno", "label":"Mention Holy Cross Lutheran Church by name?", "default":True},
    {"id":"q13", "type":"yesno", "label":"Mention the exact certificate phrase about membership in the holy Christian church?", "default":False},
    {"id":"q14", "type":"dropdown", "label":"How should baptism be framed?", "options":["family history", "personal history", "religious document", "question I am exploring"], "default":"question I am exploring"},
    {"id":"q15", "type":"yesno", "label":"Mention that you do not currently hold ordinary Lutheran doctrine?", "default":True},
    {"id":"q16", "type":"yesno", "label":"Mention First Lutheran / Pastor Kurt letter context?", "default":False},
    {"id":"q17", "type":"yesno", "label":"Mention learning Hebrew or Humanistic Judaism interest?", "default":False},
    {"id":"q18", "type":"yesno", "label":"Mention Unitarian Universalist / non-creedal religious curiosity?", "default":False},
    {"id":"q19", "type":"dropdown", "label":"Best phrase for your project", "options":["membership13", "baptism and identity project", "religion/science research project", "personal belonging research"], "default":"baptism and identity project"},
    {"id":"q20", "type":"yesno", "label":"Mention cognitive science of religion?", "default":True},
    {"id":"q21", "type":"yesno", "label":"Mention evolution of religion / agency detection?", "default":True},
    {"id":"q22", "type":"yesno", "label":"Mention Andy Thomson / Why We Believe in Gods?", "default":False},
    {"id":"q23", "type":"dropdown", "label":"How to describe God-language?", "options":["religious language", "human meaning-making", "evolved religious cognition", "I am still learning"], "default":"evolved religious cognition"},
    {"id":"q24", "type":"yesno", "label":"Mention your M.S. in Cybersecurity?", "default":True},
    {"id":"q25", "type":"yesno", "label":"Mention National University?", "default":True},
    {"id":"q26", "type":"yesno", "label":"Mention your B.S. in IT Management?", "default":True},
    {"id":"q27", "type":"yesno", "label":"Mention Security+ study?", "default":False},
    {"id":"q28", "type":"yesno", "label":"Mention cybersecurity/programming projects?", "default":True},
    {"id":"q29", "type":"text", "label":"Name one technology interest you want to mention.", "default":"cybersecurity, programming, and local AI tools"},
    {"id":"q30", "type":"yesno", "label":"Mention your school technology support work?", "default":True},
    {"id":"q31", "type":"yesno", "label":"Mention Rosa Parks Elementary by name?", "default":False},
    {"id":"q32", "type":"yesno", "label":"Mention public computer-care/student-responsibility material?", "default":False},
    {"id":"q33", "type":"yesno", "label":"Mention your book Sufficiently Educated?", "default":True},
    {"id":"q34", "type":"dropdown", "label":"How to describe the book?", "options":["learning disability memoir", "education story", "overcoming school challenges", "leave it vague"], "default":"overcoming school challenges"},
    {"id":"q35", "type":"yesno", "label":"Mention learning disabilities?", "default":True},
    {"id":"q36", "type":"yesno", "label":"Mention medical/neurology record details? Usually keep private.", "default":False},
    {"id":"q37", "type":"yesno", "label":"Mention accommodations like extra time on tests?", "default":False},
    {"id":"q38", "type":"yesno", "label":"Mention genealogy?", "default":False},
    {"id":"q39", "type":"yesno", "label":"Mention Holderman/Prickett/Smith/O'Neal research path?", "default":False},
    {"id":"q40", "type":"yesno", "label":"Mention Lutheran family continuity or older family religious history?", "default":False},
    {"id":"q41", "type":"yesno", "label":"Mention Quendor BBS history?", "default":True},
    {"id":"q42", "type":"dropdown", "label":"How should Quendor BBS be framed?", "options":["early tech interest", "retrocomputing", "San Diego BBS history", "do not mention"], "default":"early tech interest"},
    {"id":"q43", "type":"text", "label":"What do you hope to learn from the forum?", "default":"how people understand faith, science, ritual, belonging, and disagreement without attacking each other"},
    {"id":"q44", "type":"dropdown", "label":"Preferred intro length", "options":["3 sentences", "1 short paragraph", "2 paragraphs", "3 paragraphs"], "default":"2 paragraphs"},
    {"id":"q45", "type":"yesno", "label":"Ask members for recommended threads or books?", "default":True},
    {"id":"q46", "type":"yesno", "label":"Include a thanks to Thomas?", "default":True},
    {"id":"q47", "type":"text", "label":"One personal value to show in the intro.", "default":"I want to be honest, respectful, and open to correction."},
    {"id":"q48", "type":"dropdown", "label":"Safety filter", "options":["public-safe", "include some private details", "draft only, not for posting", "ask before every sensitive detail"], "default":"public-safe"},
    {"id":"q49", "type":"yesno", "label":"Save a timestamped copy every time?", "default":True},
    {"id":"q50", "type":"text", "label":"Any final detail you want included?", "default":""},
]


def ensure_dirs():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    PII_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        bad = path.with_suffix(path.suffix + f".bad-{int(time.time())}")
        shutil.copy2(path, bad)
        save_json(path, default)
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def backup_file(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = BACKUP_DIR / f"{path.name}.{stamp}.bak"
        shutil.copy2(path, dest)
        return dest
    return None


def download_url(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent":"interfaith-intro-builder/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read(500000)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(data)
    tmp.replace(dest)


def safe_bool(value):
    return bool(value) if not isinstance(value, str) else value.lower() in ("yes", "true", "1", "y")


def build_intro(answers, pii, research):
    name = answers.get("q01") or "Jeremiah"
    handle = answers.get("q02") or "we6jbo"
    mention_sd = safe_bool(answers.get("q04", True))
    belief = answers.get("q08", "atheist but interested in religion")
    tone = answers.get("q10", "Curious").lower()
    project = answers.get("q19", "baptism and identity project")
    tech_interest = answers.get("q29", "cybersecurity, programming, and local AI tools")
    hope = answers.get("q43", "how people understand faith, science, ritual, belonging, and disagreement")
    value = answers.get("q47", "I want to be honest, respectful, and open to correction.")
    final = answers.get("q50", "").strip()
    thanks = "Thanks, Thomas, for the welcome and the suggestion to introduce myself. " if safe_bool(answers.get("q46", True)) else ""

    pieces = []
    p1 = thanks + f"Hello everyone, I am {name}, posting here as @{handle}."
    if mention_sd:
        p1 += " I am from San Diego."
    p1 += f" I joined because I am {tone} about discussions where religion, science, identity, and human meaning meet."
    pieces.append(p1)

    p2_parts = []
    if safe_bool(answers.get("q24", True)) or safe_bool(answers.get("q25", True)):
        p2_parts.append("My background is in information technology and cybersecurity, including graduate study in cybersecurity at National University.")
    if safe_bool(answers.get("q28", True)):
        p2_parts.append(f"I also work on {tech_interest}.")
    if safe_bool(answers.get("q30", True)):
        p2_parts.append("A lot of my practical experience comes from supporting technology in an educational environment.")
    if safe_bool(answers.get("q33", True)):
        book_style = answers.get("q34", "overcoming school challenges")
        p2_parts.append(f"I wrote about my education path in Sufficiently Educated, which I think of as an {book_style} story.")
    if safe_bool(answers.get("q35", True)):
        p2_parts.append("That history includes learning challenges, but also long-term growth, persistence, and education.")
    if safe_bool(answers.get("q41", True)) and answers.get("q42") != "do not mention":
        p2_parts.append("My technology interests go back to running Quendor BBS in the San Diego area around 1998-2000.")
    if p2_parts:
        pieces.append(" ".join(p2_parts))

    p3_parts = []
    if safe_bool(answers.get("q11", True)):
        frame = answers.get("q14", "question I am exploring")
        church_phrase = ""
        if safe_bool(answers.get("q12", True)):
            church_phrase = " at Holy Cross Lutheran Church"
        p3_parts.append(f"One reason I am here is a {frame}: I have a childhood baptism certificate{church_phrase}, and I am thinking carefully about what that kind of record means over a lifetime.")
    if safe_bool(answers.get("q15", True)):
        p3_parts.append(f"I would currently describe myself as {belief}, so I am not trying to pretend that my present view is ordinary Lutheran doctrine.")
    if safe_bool(answers.get("q20", True)) or safe_bool(answers.get("q21", True)):
        god_lang = answers.get("q23", "evolved religious cognition")
        p3_parts.append(f"I am interested in cognitive science of religion, evolution, ritual, symbolic belonging, and God-language understood through {god_lang}.")
    if safe_bool(answers.get("q09", True)):
        p3_parts.append("I am also trying to be careful with words like 'theory,' because in science a theory is not just a random guess.")
    if safe_bool(answers.get("q38", False)):
        p3_parts.append("I also do genealogy research, which sometimes makes questions of family, church, place, and identity feel connected.")
    if p3_parts:
        pieces.append(" ".join(p3_parts))

    closing = f"I hope to learn more about {hope}. {value}"
    if safe_bool(answers.get("q45", True)):
        closing += " I would be grateful for any recommended threads, books, or careful starting points."
    if final:
        closing += " " + final
    pieces.append(closing)

    length = answers.get("q44", "2 paragraphs")
    if length == "3 sentences":
        return " ".join(pieces)[:900]
    if length == "1 short paragraph":
        return " ".join(pieces)
    if length == "3 paragraphs":
        return "\n\n".join(pieces[:2] + [" ".join(pieces[2:])])
    return "\n\n".join([pieces[0], " ".join(pieces[1:])])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.title("Interfaith Intro Builder - membership13")
        self.geometry("980x760")
        self.config_data = load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.pii = load_json(PII_FILE, DEFAULT_PII)
        self.research = load_json(RESEARCH_FILE, RESEARCH_NOTES)
        old_answers = load_json(ANSWERS_FILE, {"project": PROJECT, "answers": {}}).get("answers", {})
        self.vars = {}
        self._build_ui(old_answers)

    def _build_ui(self, old_answers):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Forum intro questionnaire", font=("TkDefaultFont", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Save answers", command=self.save_answers).pack(side="right", padx=4)
        ttk.Button(top, text="Build intro", command=self.make_intro).pack(side="right", padx=4)
        ttk.Button(top, text="Restore files", command=self.restore_files).pack(side="right", padx=4)
        ttk.Button(top, text="Open folder", command=self.open_folder).pack(side="right", padx=4)

        notice = ("Public-safe default: the script stores private profile details separately in "
                  f"{PII_DIR}. The generated intro avoids phone numbers, street addresses, and medical specifics unless you choose them.")
        ttk.Label(self, text=notice, wraplength=930).pack(fill="x", padx=10)

        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=10, pady=8)
        canvas = tk.Canvas(outer)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.form = ttk.Frame(canvas)
        self.form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for idx, q in enumerate(QUESTIONS):
            row = ttk.Frame(self.form)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{idx+1}. {q['label']}", width=65, anchor="w").pack(side="left")
            default = old_answers.get(q["id"], q.get("default", ""))
            if q["type"] == "yesno":
                var = tk.BooleanVar(value=safe_bool(default))
                cb = ttk.Checkbutton(row, variable=var, text="Yes")
                cb.pack(side="left", fill="x", expand=True)
            elif q["type"] == "dropdown":
                var = tk.StringVar(value=default)
                cb = ttk.Combobox(row, textvariable=var, values=q["options"], state="readonly", width=36)
                cb.pack(side="left", fill="x", expand=True)
            else:
                var = tk.StringVar(value=default)
                ent = ttk.Entry(row, textvariable=var, width=50)
                ent.pack(side="left", fill="x", expand=True)
            self.vars[q["id"]] = var

        bottom = ttk.Frame(self)
        bottom.pack(fill="both", padx=10, pady=8)
        ttk.Label(bottom, text="Generated intro:").pack(anchor="w")
        self.output = tk.Text(bottom, height=9, wrap="word")
        self.output.pack(fill="both", expand=False)

    def collect_answers(self):
        return {qid: var.get() for qid, var in self.vars.items()}

    def save_answers(self):
        answers = self.collect_answers()
        payload = {
            "project": PROJECT,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "answers": answers,
        }
        backup_file(ANSWERS_FILE)
        save_json(ANSWERS_FILE, payload)
        if safe_bool(answers.get("q49", True)):
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            save_json(BASE_DIR / f"interfaith_intro_answers-{stamp}.json", payload)
        messagebox.showinfo("Saved", f"Answers saved to:\n{ANSWERS_FILE}")

    def make_intro(self):
        self.save_answers()
        answers = self.collect_answers()
        intro = build_intro(answers, self.pii, self.research)
        backup_file(SUMMARY_FILE)
        SUMMARY_FILE.write_text(intro + "\n", encoding="utf-8")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", intro)
        messagebox.showinfo("Intro built", f"Forum intro saved to:\n{SUMMARY_FILE}")

    def restore_files(self):
        if not messagebox.askyesno("Restore files", "Download restore files from GitHub and back up local files first?"):
            return
        restored = []
        errors = []
        for filename in RESTORE_FILENAMES:
            url = GITHUB_RAW_BASE + filename
            dest = BASE_DIR / filename
            try:
                backup_file(dest)
                download_url(url, dest)
                restored.append(str(dest))
            except Exception as e:
                errors.append(f"{filename}: {e}")
        msg = "Restored:\n" + "\n".join(restored) if restored else "No files restored."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
        messagebox.showinfo("Restore complete", msg)

    def open_folder(self):
        try:
            if sys.platform.startswith("linux"):
                os.system(f'xdg-open "{BASE_DIR}" >/dev/null 2>&1 &')
            else:
                messagebox.showinfo("Folder", str(BASE_DIR))
        except Exception:
            messagebox.showinfo("Folder", str(BASE_DIR))


def main():
    ensure_dirs()
    load_json(CONFIG_FILE, DEFAULT_CONFIG)
    load_json(PII_FILE, DEFAULT_PII)
    load_json(RESEARCH_FILE, RESEARCH_NOTES)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
