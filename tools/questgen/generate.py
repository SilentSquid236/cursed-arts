#!/usr/bin/env python3
"""Generates the Cursed Arts FTB Quests book.

Usage: python3 tools/questgen/generate.py config/ftbquests/quests
"""
import hashlib, os, json, sys

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))

def qid(*parts):
    return hashlib.sha1("/".join(parts).encode()).hexdigest()[:16].upper()

def s(v):  # SNBT string
    return json.dumps(v, ensure_ascii=False)

LANG = {}
SEEN = set()

def item(i, n=1):
    return '{ count: %d, id: %s }' % (n, s(i))

def task_item(qkey, i, n=1):
    cnt = ("count: %dL, " % n) if n > 1 else ""
    return '{ %sid: %s, item: %s, type: "item" }' % (cnt, s(qid(qkey, "t", i)), item(i, 1))

def task_kill(qkey, e, n):
    return '{ entity: %s, id: %s, type: "kill", value: %dL }' % (s(e), s(qid(qkey, "t", e)), n)

def task_adv(qkey, a):
    return '{ advancement: %s, criterion: "", id: %s, type: "advancement" }' % (s(a), s(qid(qkey, "t", a)))

def task_dim(qkey, d):
    return '{ dimension: %s, id: %s, type: "dimension" }' % (s(d), s(qid(qkey, "t", d)))

def task_check(qkey):
    return '{ id: %s, type: "checkmark" }' % s(qid(qkey, "t", "check"))

def r_xp(qkey, n):
    return '{ id: %s, type: "xp", xp: %d }' % (s(qid(qkey, "r", "xp")), n)

def r_item(qkey, i, n=1):
    return '{ count: %d, id: %s, item: %s, type: "item" }' % (n, s(qid(qkey, "r", i)), item(i))

def r_grade_xp(qkey, n):
    # Cursed Techniques grade XP, granted by command.
    return ('{ command: %s, id: %s, permission_level: 2, silent: true, type: "command" }'
            % (s("/cursed xp {p} %d" % n), s(qid(qkey, "r", "gradexp"))))

def quest(ch, key, x, y, tasks, rewards=(), deps=(), title=None, sub=None, desc=None,
          icon=None, shape=None, size=None):
    i = qid(ch, key)
    assert i not in SEEN, f"duplicate quest {ch}/{key}"
    SEEN.add(i)
    if title: LANG[f"quest.{i}.title"] = title
    if sub: LANG[f"quest.{i}.quest_subtitle"] = sub
    if desc: LANG[f"quest.{i}.quest_desc"] = desc
    lines = ["\t\t{"]
    if deps: lines.append("\t\t\tdependencies: [%s]" % ", ".join(s(qid(ch, d)) for d in deps))
    if icon: lines.append("\t\t\ticon: { id: %s }" % s(icon))
    lines.append("\t\t\tid: %s" % s(i))
    if rewards: lines.append("\t\t\trewards: [%s]" % ", ".join(rewards))
    if shape: lines.append("\t\t\tshape: %s" % s(shape))
    if size: lines.append("\t\t\tsize: %.1fd" % size)
    lines.append("\t\t\ttasks: [%s]" % ", ".join(tasks))
    lines.append("\t\t\tx: %.1fd" % x)
    lines.append("\t\t\ty: %.1fd" % y)
    lines.append("\t\t}")
    return "\n".join(lines)

CHAPTERS = []

def chapter(name, title, icon, order, quests, group=""):
    i = qid("chapter", name)
    LANG[f"chapter.{i}.title"] = title
    body = ("{\n\tdefault_hide_dependency_lines: false\n\tdefault_quest_shape: \"\"\n"
            f"\tfilename: {s(name)}\n\tgroup: {s(group)}\n\ticon: {{ id: {s(icon)} }}\n\tid: {s(i)}\n"
            f"\torder_index: {order}\n\tquest_links: [ ]\n\tquests: [\n" + "\n".join(quests) + "\n\t]\n}\n")
    CHAPTERS.append((name, body))

# ------------------------------------------------------------- chapter groups
GROUPS = [("cursed", "Cursed Arts"), ("magic", "Magic"), ("tech", "Technology"), ("combat", "Combat & Gear"),
          ("explore", "Exploration"), ("farming", "Farming & Food"), ("utility", "Utility")]
G = {k: qid("group", k) for k, _ in GROUPS}
for k, t in GROUPS:
    LANG[f"chapter_group.{G[k]}.title"] = t

# ------------------------------------------------------------------ Awakening
c = "awakening"
q = lambda *a, **k: quest(c, *a, **k)
chapter(c, "Awakening", "minecraft:ender_eye", 0, group=G["cursed"], quests=[
    q("welcome", 0, 0, [task_check("welcome")], [r_item("welcome", "minecraft:bread", 16), r_xp("welcome", 10)],
      title="Welcome to Cursed Arts", sub="Read me first", shape="hexagon", size=2.0, icon="minecraft:ender_eye",
      desc=["Everyone here is born with an &dinnate technique&r. Most awaken as &7Grade 2&r sorcerers; a rare few are born far stronger.",
            "",
            "&eZ&r and &eX&r use your two abilities. &eV&r is Domain Expansion (unlocks at &6Grade 1&r). &eG&r is your Maximum technique (Special Grade only).",
            "",
            "Type &b/cursed info&r any time to see your technique, grade and what you need for the next promotion.",
            "",
            "Other chapters cover the magic, tech and exploration mods in the pack. Do them in any order."]),
    q("awakened", 2.5, 0, [task_adv("awakened", "cursedtech:awakened")], [r_grade_xp("awakened", 25)], deps=["welcome"],
      title="Your Innate Technique", sub="Find out what you were born with",
      desc=["Your technique and grade are shown above your hotbar.", "",
            "Abilities cost &dcursed energy&r, which refills over about 30 seconds. Watch the cooldowns."]),
    q("first_exorcism", 5, -1.5, [task_kill("first_exorcism", "minecraft:zombie", 10)],
      [r_grade_xp("first_exorcism", 50), r_item("first_exorcism", "minecraft:iron_ingot", 8)], deps=["awakened"],
      title="First Exorcisms", sub="Hostile kills give grade XP",
      desc=["Every hostile mob you defeat gives &bgrade XP&r: about a quarter of its max health. Farm animals and villagers give nothing."]),
    q("night_patrol", 7.5, -1.5, [task_kill("night_patrol", "minecraft:skeleton", 20), task_kill("night_patrol", "minecraft:creeper", 10)],
      [r_grade_xp("night_patrol", 100)], deps=["first_exorcism"], title="Night Patrol", icon="minecraft:bow"),
    q("black_flash", 5, 1.5, [task_adv("black_flash", "cursedtech:black_flash")],
      [r_grade_xp("black_flash", 75), r_item("black_flash", "minecraft:diamond", 2)], deps=["awakened"],
      title="Black Flash", sub="Space bends with a perfect hit", icon="minecraft:black_dye", shape="diamond",
      desc=["Hit something with a &efully charged&r melee attack. There's a small chance it becomes a &cBlack Flash&r: about 1.8x damage and a flash that warps the screen.",
            "", "Landing one puts you &cin the zone&r for 10 seconds, with much higher odds. Higher grades require several."]),
    q("semi_grade_1", 10, 0, [task_adv("semi_grade_1", "cursedtech:semi_grade_1")],
      [r_item("semi_grade_1", "minecraft:diamond", 4), r_item("semi_grade_1", "minecraft:golden_apple", 2)],
      deps=["night_patrol"], title="Semi-Grade 1", sub="2,500 grade XP", icon="minecraft:iron_sword",
      desc=["Your cursed energy reserves deepen: more energy, faster regen, harder hits."]),
    q("boss", 10, 3, [task_adv("boss", "cursedtech:boss")], [r_item("boss", "minecraft:diamond", 6)], deps=["black_flash"],
      title="Exorcist", sub="Defeat a boss", icon="minecraft:wither_skeleton_skull",
      desc=["Bosses (150+ max health) give a huge amount of grade XP and count toward Special Grade. See the &cExorcisms&r chapter for targets."]),
    q("grade_1", 12.5, 0, [task_adv("grade_1", "cursedtech:grade_1")],
      [r_item("grade_1", "minecraft:diamond", 8), r_item("grade_1", "minecraft:totem_of_undying", 1)],
      deps=["semi_grade_1", "black_flash"], title="Grade 1", sub="8,000 XP and 3 Black Flashes", icon="minecraft:diamond_sword",
      shape="hexagon", size=1.5,
      desc=["Promotion to Grade 1 unlocks &dDomain Expansion&r (V)."]),
    q("domain", 15, -1.5, [task_adv("domain", "cursedtech:domain")], [r_xp("domain", 30)], deps=["grade_1"],
      title="Domain Expansion", sub="Trap them in your world", icon="minecraft:obsidian",
      desc=["A domain raises a barrier around you and everything inside suffers your technique's sure-hit effect.",
            "", "If two domains overlap they &6clash&r: the stronger one shatters the other. Afterwards your technique &cburns out&r for 10 seconds, so pick your moment."]),
    q("special", 15, 1.5, [task_adv("special", "cursedtech:special")],
      [r_item("special", "minecraft:nether_star", 1), r_item("special", "minecraft:netherite_ingot", 2)],
      deps=["grade_1", "boss"], title="Special Grade", sub="30,000 XP, 12 Black Flashes, 2 bosses", icon="minecraft:netherite_sword",
      shape="hexagon", size=2.0,
      desc=["The peak. Unlocks your &cMaximum&r technique (G) and &aReverse Cursed Technique&r, which slowly heals you with cursed energy."]),
    q("maximum", 17.5, 1.5, [task_adv("maximum", "cursedtech:maximum")], [r_xp("maximum", 50)], deps=["special"],
      title="Maximum", sub="Everything you have", icon="minecraft:nether_star", shape="gear"),
])

# ----------------------------------------------------------------- Exorcisms
c = "exorcisms"
q = lambda *a, **k: quest(c, *a, **k)
bosses = [
    ("elder_guardian", "minecraft:elder_guardian", "Elder Guardian", "minecraft:prismarine_shard"),
    ("wither", "minecraft:wither", "The Wither", "minecraft:wither_skeleton_skull"),
    ("ender_dragon", "minecraft:ender_dragon", "Ender Dragon", "minecraft:dragon_head"),
    ("warden", "minecraft:warden", "The Warden", "minecraft:sculk_shrieker"),
    ("ferrous_wroughtnaut", "mowziesmobs:ferrous_wroughtnaut", "Ferrous Wroughtnaut", "minecraft:iron_axe"),
    ("frostmaw", "mowziesmobs:frostmaw", "Frostmaw", "minecraft:blue_ice"),
    ("umvuthi", "mowziesmobs:umvuthi", "Umvuthi", "minecraft:gold_block"),
    ("sculptor", "mowziesmobs:sculptor", "The Sculptor", "minecraft:chiseled_stone_bricks"),
    ("ender_guardian", "cataclysm:ender_guardian", "Ender Guardian", "minecraft:end_stone_bricks"),
    ("netherite_monstrosity", "cataclysm:netherite_monstrosity", "Netherite Monstrosity", "minecraft:netherite_block"),
    ("ignis", "cataclysm:ignis", "Ignis", "minecraft:blaze_rod"),
    ("the_harbinger", "cataclysm:the_harbinger", "The Harbinger", "minecraft:redstone_block"),
    ("the_leviathan", "cataclysm:the_leviathan", "The Leviathan", "minecraft:heart_of_the_sea"),
    ("ancient_remnant", "cataclysm:ancient_remnant", "Ancient Remnant", "minecraft:sandstone"),
    ("maledictus", "cataclysm:maledictus", "Maledictus", "minecraft:soul_lantern"),
    ("scylla", "cataclysm:scylla", "Scylla", "minecraft:trident"),
]
qs = [q("hunt", 0, 0, [task_check("hunt")], [r_xp("hunt", 5)], title="The Hunt", sub="Cursed spirits of every grade",
        icon="minecraft:iron_sword", shape="hexagon", size=2.0,
        desc=["These are the strongest things in the world. Each one is worth a huge pile of &bgrade XP&r, and bosses count toward &cSpecial Grade&r.",
              "", "Explore to find them: Cataclysm bosses guard their own structures, Mowzie's bosses roam specific biomes. &eExplorer's Compass&r helps.",
              "", "Bring friends. Domain Expansion is your best tool here."])]
for n, (k, e, t, ic) in enumerate(bosses):
    col, row = n % 4, n // 4
    qs.append(q(k, 3 + col * 2.5, -3 + row * 2.0, [task_kill(k, e, 1)],
                [r_grade_xp(k, 150), r_item(k, "minecraft:diamond", 3)], deps=["hunt"], title=t, icon=ic))
chapter(c, "Exorcisms", "minecraft:wither_skeleton_skull", 1, qs, group=G["cursed"])

# ---------------------------------------------------------------- Expedition
c = "expedition"
q = lambda *a, **k: quest(c, *a, **k)
qs = [q("intro", 0, 0, [task_check("intro")], [r_xp("intro", 5)], title="Expedition", icon="minecraft:compass", shape="hexagon", size=1.5,
        desc=["New terrain, biomes and structures everywhere: Terralith and Tectonic reshape the land, and When Dungeons Arise and Dungeon Crawl hide dungeons full of loot.",
              "", "Loot chests are per-player (Lootr), so everyone gets their own."]),
      q("waystone", 2.5, -2, [task_item("waystone", "waystones:waystone")], [r_xp("waystone", 10)], deps=["intro"],
        desc=["Place Waystones to fast-travel between them."]),
      q("backpack", 2.5, 0, [task_item("backpack", "sophisticatedbackpacks:backpack")], [r_xp("backpack", 10)], deps=["intro"]),
      q("cooking_pot", 2.5, 2, [task_item("cooking_pot", "farmersdelight:cooking_pot")], [r_xp("cooking_pot", 10)], deps=["intro"],
        desc=["Better food, longer fights."]),
      q("explorers", 5, -2, [task_item("explorers", "explorerscompass:explorerscompass")], [r_xp("explorers", 15)], deps=["waystone"],
        desc=["Points you at any structure, including boss arenas."]),
      q("natures", 5, 0, [task_item("natures", "naturescompass:naturescompass")], [r_xp("natures", 15)], deps=["backpack"]),
      q("reforging", 5, 2, [task_item("reforging", "apotheosis:reforging_table")], [r_xp("reforging", 20)], deps=["cooking_pot"],
        desc=["Apotheosis gear has random affixes. Reforge it for better rolls."]),
      q("nether", 7.5, -1, [task_dim("nether", "minecraft:the_nether")], [r_grade_xp("nether", 50)], deps=["explorers"],
        title="Into the Nether", icon="minecraft:obsidian"),
      q("end", 10, -1, [task_dim("end", "minecraft:the_end")], [r_grade_xp("end", 100)], deps=["nether"],
        title="The End", icon="minecraft:end_portal_frame"),
]
chapter(c, "Expedition", "minecraft:compass", 2, qs, group=G["cursed"])


# ======================================================= kitchen-sink chapters
# Chapters generated from each mod's own advancement tree (advancements.json is
# extracted from the mod jars by extract_advancements.py). Titles come from the
# advancement itself and descriptions use the mod's translation keys, so they
# show in the player's language and stay in sync with the mod.
ADV = json.load(open(os.path.join(HERE, "advancements.json")))
NAMES = ADV["names"]

ADV_CHAPTERS = [
    # name, title, group, namespaces
    ("create", "Create", "tech", ["create", "create_connected"]),
    ("mekanism", "Mekanism", "tech", ["mekanism", "mekanismgenerators", "mekanismtools", "mekanismadditions"]),
    ("immersive_engineering", "Immersive Engineering", "tech", ["immersiveengineering"]),
    ("pneumaticcraft", "PneumaticCraft", "tech", ["pneumaticcraft"]),
    ("ae2", "Applied Energistics 2", "tech", ["ae2"]),
    ("ars_nouveau", "Ars Nouveau", "magic", ["ars_nouveau", "ars_additions"]),
    ("irons_spellbooks", "Iron's Spells 'n Spellbooks", "magic", ["irons_spellbooks"]),
    ("occultism", "Occultism", "magic", ["occultism"]),
    ("astral_sorcery", "Astral Sorcery", "magic", ["astralsorcery"]),
    ("silent_gear", "Silent Gear", "combat", ["silentgear"]),
    ("apotheosis", "Apotheosis", "combat", ["apotheosis", "apothic_enchanting", "apothic_spawners"]),
    ("cataclysm", "L_Ender's Cataclysm", "combat", ["cataclysm"]),
    ("mowzies_mobs", "Mowzie's Mobs", "combat", ["mowziesmobs"]),
    ("dungeons_arise", "When Dungeons Arise", "explore", ["dungeons_arise"]),
    ("biomes", "Oh The Biomes We've Gone", "explore", ["biomeswevegone"]),
    ("lootr", "Lootr", "explore", ["lootr"]),
    ("farmers_delight", "Farmer's Delight", "farming", ["farmersdelight"]),
]

def text_of(k):
    if not k: return None
    if k.startswith("T:"): return "{" + k[2:] + "}"
    v = k[2:].strip()
    return v or None

FRAME_REWARDS = {"task": (10, 0), "goal": (25, 25), "challenge": (50, 100)}

def adv_chapter(order, name, title, group, namespaces):
    rows = [r for r in ADV["adv"] if r[0].split(":")[0] in namespaces]
    if len(rows) < 3: return None
    by_id = {r[0]: r for r in rows}
    kids = {}
    roots = []
    for r in rows:
        par = r[1] if r[1] in by_id else None
        if par: kids.setdefault(par, []).append(r[0])
        else: roots.append(r[0])
    for k in kids: kids[k].sort()
    roots.sort(key=lambda a: (len(kids.get(a, [])) == 0, a))  # real trees first, loose ends last
    pos, leaf = {}, [0]
    def place(a, depth):
        ch = kids.get(a, [])
        if not ch:
            y = leaf[0]; leaf[0] += 1
        else:
            ys = [place(c, depth + 1) for c in ch]
            y = sum(ys) / len(ys)
        pos[a] = (depth * 1.75, y * 1.25)
        return y
    for rt in roots:
        place(rt, 0)
        leaf[0] += 1  # gap between trees
    c = name
    qs = []
    for a, (x, y) in sorted(pos.items(), key=lambda kv: kv[1]):
        r = by_id[a]
        key = a.replace(":", "/")
        xp, gxp = FRAME_REWARDS.get(r[3], (10, 0))
        rewards = [r_xp(key, xp)]
        if gxp: rewards.append(r_grade_xp(key, gxp))
        if r[3] == "challenge": rewards.append(r_item(key, "minecraft:diamond", 2))
        desc = text_of(r[5])
        deps = [r[1].replace(":", "/")] if r[1] in by_id else []
        shape = {"goal": "hexagon", "challenge": "gear"}.get(r[3])
        qs.append(quest(c, key, x, y, [task_adv(key, a)], rewards, deps=deps,
                        desc=[desc] if desc else None, icon=r[2], shape=shape))
    root_icon = by_id[roots[0]][2] if roots else "minecraft:book"
    chapter(name, title, root_icon, order, qs, group=G[group])
    return len(qs)

# Item-progression chapters for mods that ship no advancements. Each row is a path
# through the mod; every item ID was checked against the installed jars.
ITEM_CHAPTERS = [
    ("draconic_evolution", "Draconic Evolution", "tech", "draconicevolution:draconium_ingot", [
        ("Draconium", "Draconium ore is found in the Overworld, Nether and End. Everything starts here.",
         ["draconicevolution:draconium_ingot", "draconicevolution:draconium_core", "draconicevolution:crafting_core"]),
        ("Wyvern tier", "Fusion crafting unlocks the Wyvern tier of gear and machines.",
         ["draconicevolution:wyvern_core", "draconicevolution:wyvern_pickaxe", "draconicevolution:energy_core"]),
        ("Awakened", "The endgame: awakened draconium and chaos.",
         ["draconicevolution:awakened_draconium_ingot", "draconicevolution:awakened_core", "draconicevolution:chaotic_core"]),
    ]),
    ("powah", "Powah", "tech", "powah:energy_cell_starter", [
        ("Getting started", "Dielectric paste and an Energizing Orb power almost every Powah recipe.",
         ["powah:dielectric_paste", "powah:energizing_orb", "powah:energizing_rod_starter"]),
        ("Generation", "Pick a generator and store what it makes.",
         ["powah:furnator_starter", "powah:solar_panel_starter", "powah:energy_cell_starter", "powah:capacitor_basic", "powah:reactor_starter"]),
    ]),
    ("industrial_foregoing", "Industrial Foregoing", "tech", "industrialforegoing:machine_frame_pity", [
        ("Plastic age", "Latex from trees becomes plastic, which becomes machine frames.",
         ["industrialforegoing:latex_processing_unit", "industrialforegoing:fluid_extractor", "industrialforegoing:plastic", "industrialforegoing:machine_frame_pity"]),
        ("Machines", "Automate the boring parts of the world.",
         ["industrialforegoing:dissolution_chamber", "industrialforegoing:mob_crusher", "industrialforegoing:infinity_drill"]),
    ]),
    ("flux_networks", "Flux Networks", "tech", "fluxnetworks:flux_core", [
        ("Wireless power", "Drop redstone on obsidian over bedrock to make Flux Dust, then send power anywhere.",
         ["fluxnetworks:flux_dust", "fluxnetworks:flux_core", "fluxnetworks:flux_plug", "fluxnetworks:flux_point", "fluxnetworks:flux_controller", "fluxnetworks:basic_flux_storage", "fluxnetworks:flux_configurator"]),
    ]),
    ("oritech", "Oritech", "tech", "oritech:assembler_block", [
        ("Industry", "Big, animated machines for processing and power.",
         ["oritech:basic_generator_block", "oritech:pulverizer_block", "oritech:assembler_block", "oritech:foundry_block", "oritech:fragment_forge_block", "oritech:laser_arm_block"]),
    ]),
    ("logistics", "Pipes & Logistics", "tech", "pipez:item_pipe", [
        ("Pipez", "Simple pipes for items, fluids and energy. Upgrades make them faster.",
         ["pipez:item_pipe", "pipez:fluid_pipe", "pipez:energy_pipe", "pipez:universal_pipe", "pipez:basic_upgrade"]),
        ("LaserIO", "Wireless logistics with laser nodes and cards.",
         ["laserio:laser_wrench", "laserio:laser_connector", "laserio:laser_node", "laserio:card_item"]),
    ]),
    ("gadgets", "Gadgets & Tools", "utility", "mininggadgets:mininggadget", [
        ("Mining Gadgets", "Laser mining tools you can upgrade at the Modification Table.",
         ["mininggadgets:mininggadget_simple", "mininggadgets:modificationtable", "mininggadgets:upgrade_empty", "mininggadgets:mininggadget", "mininggadgets:mininggadget_fancy"]),
        ("Building Gadgets", "Build, exchange, copy and paste whole structures.",
         ["buildinggadgets2:gadget_building", "buildinggadgets2:gadget_exchanging", "buildinggadgets2:gadget_copy_paste", "buildinggadgets2:gadget_destruction", "buildinggadgets2:template_manager"]),
        ("Iron Jetpacks", "Fly.", ["ironjetpacks:strap", "ironjetpacks:basic_coil", "ironjetpacks:cell"]),
        ("Just Dire Things", "New materials and clever tools.",
         ["justdirethings:gooblock_tier1", "justdirethings:ferricore_ingot", "justdirethings:blazegold_ingot", "justdirethings:celestigem", "justdirethings:eclipsealloy_ingot"]),
    ]),
    ("malum", "Malum", "magic", "malum:spirit_altar", [
        ("Spirit magic", "Harvest spirits from the creatures you slay, then infuse them into gear.",
         ["malum:encyclopedia_arcana", "malum:runewood_log", "malum:spirit_altar", "malum:spirit_jar", "malum:soul_stained_steel_ingot", "malum:hallowed_gold_ingot", "malum:spirit_crucible"]),
    ]),
    ("forbidden_arcanus", "Forbidden & Arcanus", "magic", "forbidden_arcanus:arcane_crystal", [
        ("Dark arts", "Arcane crystals, deorum and the Clibano furnace.",
         ["forbidden_arcanus:arcane_crystal", "forbidden_arcanus:mundabitur_dust", "forbidden_arcanus:deorum_ingot", "forbidden_arcanus:smelter_prism", "forbidden_arcanus:clibano_core"]),
    ]),
    ("mystical_agriculture", "Mystical Agriculture", "farming", "mysticalagriculture:inferium_essence", [
        ("Essence tiers", "Combine essence to climb the tiers and grow better seeds.",
         ["mysticalagriculture:inferium_essence", "mysticalagriculture:prosperity_shard", "mysticalagriculture:prudentium_essence", "mysticalagriculture:tertium_essence", "mysticalagriculture:imperium_essence", "mysticalagriculture:supremium_essence"]),
        ("Infusion", "Craft seeds and upgrades on the Infusion Altar.",
         ["mysticalagriculture:infusion_pedestal", "mysticalagriculture:infusion_altar", "mysticalagriculture:awakening_altar"]),
    ]),
    ("storage_travel", "Storage & Travel", "utility", "waystones:waystone", [
        ("Backpacks", "Upgrade your backpack tier by tier.",
         ["sophisticatedbackpacks:backpack", "sophisticatedbackpacks:pickup_upgrade", "sophisticatedbackpacks:iron_backpack", "sophisticatedbackpacks:gold_backpack", "sophisticatedbackpacks:diamond_backpack", "sophisticatedbackpacks:netherite_backpack"]),
        ("Waystones", "Fast travel between waystones, or carry a scroll.",
         ["waystones:waystone", "waystones:warp_stone", "waystones:warp_scroll", "waystones:return_scroll"]),
        ("Mob control", "Keep spawns away from your base.",
         ["torchmaster:megatorch", "torchmaster:feral_flare_lantern", "torchmaster:dreadlamp"]),
    ]),
]

def item_chapter(order, name, title, group, icon, rows):
    c = name
    qs = []
    for ri, (rtitle, rdesc, items) in enumerate(rows):
        y = ri * 2.0
        prev = None
        for n, it in enumerate(items):
            key = f"{name}_r{ri}_{n}"
            kw = dict(title=rtitle, desc=[rdesc], shape="hexagon") if n == 0 else {}
            qs.append(quest(c, key, n * 1.75, y, [task_item(key, it)], [r_xp(key, 10 + 5 * n)],
                            deps=[prev] if prev else [], **kw))
            prev = key
    chapter(name, title, icon, order, qs, group=G[group])
    return len(qs)

order = 10
stats = []
for spec in ADV_CHAPTERS:
    n = adv_chapter(order, *spec)
    if n: stats.append((spec[1], n)); order += 1
for spec in ITEM_CHAPTERS:
    stats.append((spec[1], item_chapter(order, *spec))); order += 1
print(", ".join(f"{t} {n}" for t, n in stats))

# -------------------------------------------------------------------- write
os.makedirs(f"{OUT}/chapters", exist_ok=True)
os.makedirs(f"{OUT}/lang", exist_ok=True)
for name, body in CHAPTERS:
    open(f"{OUT}/chapters/{name}.snbt", "w").write(body)
LANG["file.0000000000000001.title"] = "Cursed Arts"
with open(f"{OUT}/lang/en_us.snbt", "w") as f:
    f.write("{\n")
    for k in sorted(LANG):
        v = LANG[k]
        if isinstance(v, list):
            f.write("\t%s: [%s]\n" % (k, ", ".join(s(x) for x in v)))
        else:
            f.write("\t%s: %s\n" % (k, s(v)))
    f.write("}\n")
open(f"{OUT}/data.snbt", "w").write("""{
	default_autoclaim_rewards: "disabled"
	default_consume_items: false
	default_quest_disable_jei: false
	default_quest_shape: "circle"
	default_reward_team: false
	detection_delay: 20
	disable_gui: false
	drop_book_on_death: false
	drop_loot_crates: false
	emergency_items_cooldown: 300
	fallback_locale: ""
	grid_scale: 0.5d
	hide_excluded_quests: false
	icon: { id: "minecraft:ender_eye" }
	lock_message: ""
	loot_crate_no_drop: {
		boss: 0
		monster: 0
		passive: 0
	}
	pause_game: false
	progression_mode: "flexible"
	show_lock_icons: true
	verify_on_load: false
	version: 13
}
""")
open(f"{OUT}/chapter_groups.snbt", "w").write("{\n\tchapter_groups: [\n" + "".join('\t\t{ id: %s }\n' % s(G[k]) for k, _ in GROUPS) + "\t]\n}\n")
nq = sum(b.count("\t\t\tid: ") for _, b in CHAPTERS)
print(f"{len(CHAPTERS)} chapters, {nq} quests, {len(LANG)} lang entries")
