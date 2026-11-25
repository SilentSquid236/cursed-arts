#!/usr/bin/env python3
"""Generates the Cursed Arts FTB Quests book: a linear story, "Seal the Calamity".

Eight chapters, each a single main path. Chapter N's first quest depends on the
last quest of chapter N-1. Optional side quests branch off the main path: they
make the next steps easier but are never required.

Every item/entity ID below was checked against the pack's jars.

Usage: python3 tools/questgen/generate.py config/ftbquests/quests
"""
import hashlib, os, json, sys, shutil

OUT = sys.argv[1]

def qid(*parts):
    # Keep the top bit clear: FTB Quests treats IDs as signed longs, and a negative
    # ID no longer matches its lang keys (titles show as "Unnamed").
    h = int(hashlib.sha1("/".join(parts).encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
    return "%016X" % h

def s(v):  # SNBT string
    return json.dumps(v, ensure_ascii=False)

LANG = {}
SEEN = set()

# ------------------------------------------------------------------- tasks
def item(i, n=1):
    return '{ count: %d, id: %s }' % (n, s(i))

def t_item(i, n=1):
    return ("item", i, n)

def t_kill(e, n=1):
    return ("kill", e, n)

def t_adv(a):
    return ("adv", a, 0)

def t_dim(d):
    return ("dim", d, 0)

def t_check():
    return ("check", "check", 0)

def render_task(qkey, t, n):
    kind, v, cnt = t
    tid = s(qid(qkey, "t", str(n), v))
    if kind == "item":
        c = ("count: %dL, " % cnt) if cnt > 1 else ""
        return '{ %sid: %s, item: %s, type: "item" }' % (c, tid, item(v))
    if kind == "kill":
        return '{ entity: %s, id: %s, type: "kill", value: %dL }' % (s(v), tid, cnt)
    if kind == "adv":
        return '{ advancement: %s, criterion: "", id: %s, type: "advancement" }' % (s(v), tid)
    if kind == "dim":
        return '{ dimension: %s, id: %s, type: "dimension" }' % (s(v), tid)
    return '{ id: %s, type: "checkmark" }' % tid

# ----------------------------------------------------------------- rewards
def r_item(i, n=1):
    return ("item", i, n)

def r_xp(n):
    return ("xp", "", n)

def r_grade(n):  # Cursed Techniques grade XP
    return ("cmd", "/cursed xp {p} %d" % n, 0)

def r_cmd(c):
    return ("cmd", c, 0)

def render_reward(qkey, r, n):
    kind, v, cnt = r
    rid = s(qid(qkey, "r", str(n), v))
    if kind == "item":
        return '{ count: %d, id: %s, item: %s, type: "item" }' % (cnt, rid, item(v))
    if kind == "xp":
        return '{ id: %s, type: "xp", xp: %d }' % (rid, cnt)
    return '{ command: %s, id: %s, permission_level: 2, silent: true, type: "command" }' % (s(v), rid)

# ---------------------------------------------------------------- chapters
CHAPTERS = []
LAST = {}  # chapter -> key of its final main quest


class Chapter:
    def __init__(self, name, title, subtitle, icon):
        self.name, self.title, self.subtitle, self.icon = name, title, subtitle, icon
        self.quests = []
        self.y = 0.0
        self.prev_y = 0.0
        self.prev = None          # previous main quest key
        self.side_slots = {}      # main key -> number of side quests placed
        self.entry_dep = None     # cross-chapter dependency for the first quest

    def _quest(self, key, x, y, tasks, rewards, deps, title, sub, desc, icon, shape, size, optional):
        qkey = f"{self.name}/{key}"
        i = qid(qkey)
        assert i not in SEEN, f"duplicate quest {qkey}"
        SEEN.add(i)
        if title: LANG[f"quest.{i}.title"] = title
        if sub: LANG[f"quest.{i}.quest_subtitle"] = sub
        if desc: LANG[f"quest.{i}.quest_desc"] = desc
        L = ["\t\t{"]
        if deps: L.append("\t\t\tdependencies: [%s]" % ", ".join(s(d) for d in deps))
        if icon: L.append("\t\t\ticon: { id: %s }" % s(icon))
        L.append("\t\t\tid: %s" % s(i))
        if optional: L.append("\t\t\toptional: true")
        if rewards: L.append("\t\t\trewards: [%s]" % ", ".join(render_reward(qkey, r, n) for n, r in enumerate(rewards)))
        if shape: L.append("\t\t\tshape: %s" % s(shape))
        if size: L.append("\t\t\tsize: %.1fd" % size)
        L.append("\t\t\ttasks: [%s]" % ", ".join(render_task(qkey, t, n) for n, t in enumerate(tasks)))
        L.append("\t\t\tx: %.1fd" % x)
        L.append("\t\t\ty: %.1fd" % y)
        L.append("\t\t}")
        self.quests.append("\n".join(L))
        return i

    def main(self, key, tasks, rewards=(), title=None, sub=None, desc=None, icon=None, shape=None, size=None):
        deps = []
        if self.prev:
            deps.append(qid(f"{self.name}/{self.prev}"))
        elif self.entry_dep:
            deps.append(self.entry_dep)
        pad = ((size or 1.0) - 1.0) * 0.5
        y = self.y + pad
        self._quest(key, 0.0, y, tasks, rewards, deps, title, sub, desc, icon, shape, size, False)
        self.prev, self.prev_y = key, y
        self.y = y + pad + 1.5
        return key

    def side(self, key, tasks, rewards=(), title=None, sub=None, desc=None, icon=None, shape="diamond"):
        """Optional quest hanging off the most recent main quest."""
        anchor = self.prev
        n = self.side_slots.get(anchor, 0)
        self.side_slots[anchor] = n + 1
        x = (-2.5, 2.5, -4.0, 4.0)[n]
        self._quest(key, x, self.prev_y, tasks, rewards, [qid(f"{self.name}/{anchor}")],
                    title, sub, desc, icon, shape, None, True)

    def finish(self, order):
        i = qid("chapter", self.name)
        LANG[f"chapter.{i}.title"] = self.title
        if self.subtitle: LANG[f"chapter.{i}.chapter_subtitle"] = [self.subtitle]
        body = ("{\n\tdefault_hide_dependency_lines: false\n\tdefault_quest_shape: \"\"\n"
                f"\tfilename: {s(self.name)}\n\tgroup: \"\"\n\ticon: {{ id: {s(self.icon)} }}\n\tid: {s(i)}\n"
                f"\torder_index: {order}\n\tquest_links: [ ]\n\tquests: [\n" + "\n".join(self.quests) + "\n\t]\n}\n")
        CHAPTERS.append((self.name, body))
        LAST[self.name] = qid(f"{self.name}/{self.prev}")


def new_chapter(*a):
    ch = Chapter(*a)
    if CHAPTERS_ORDER:
        ch.entry_dep = LAST[CHAPTERS_ORDER[-1].name]
    return ch

CHAPTERS_ORDER = []

def done(ch):
    ch.finish(len(CHAPTERS_ORDER))
    CHAPTERS_ORDER.append(ch)


# =========================================================================
# Chapter 1 - Prologue
# =========================================================================
c = new_chapter("1_prologue", "I. The Seal Cracks", "Prologue", "minecraft:ender_eye")
c.main("welcome", [t_check()], [r_item("minecraft:bread", 16), r_item("minecraft:torch", 32)],
       title="The Seal Cracks", sub="Read me first", icon="minecraft:ender_eye", shape="hexagon", size=2.0,
       desc=["A thousand years ago the strongest sorcerers of their age buried something so dangerous they refused to write down its name. They called it &5the Calamity&r and sealed it beneath the world.",
             "",
             "Last night, the seal cracked.",
             "",
             "Everyone near the fracture woke up with &dcursed energy&r in their veins. You are one of them. Somewhere out there the Calamity is pulling itself back together, and the old seal will not hold much longer.",
             "",
             "This book is your path from a frightened Grade 2 sorcerer to the one who seals it again. Follow the main line from top to bottom. &7Diamond-shaped quests off to the sides are optional&r: they make the road easier, but you can skip them."])
c.main("awakened", [t_adv("cursedtech:awakened")], [r_grade(25)],
       title="Your Innate Technique", sub="What were you born with?", icon="minecraft:amethyst_shard",
       desc=["Your technique and grade show above your hotbar. &eZ&r and &eX&r are your two abilities.",
             "",
             "Abilities cost cursed energy, which refills over about 30 seconds. Type &b/cursed info&r any time to see your technique and what your next promotion needs."])
c.main("stone", [t_item("minecraft:stone_pickaxe"), t_item("minecraft:furnace")], [r_item("minecraft:coal", 16)],
       title="First Tools", icon="minecraft:stone_pickaxe",
       desc=["Get off the surface: a stone pickaxe, and a furnace to smelt what you find."])
c.main("iron", [t_item("minecraft:iron_ingot", 16)], [r_item("minecraft:bread", 8)],
       title="Iron", icon="minecraft:iron_ingot",
       desc=["Mine iron ore and smelt it. Almost everything you build next starts with iron."])
c.main("steel", [t_item("minecraft:iron_sword"), t_item("minecraft:iron_pickaxe"), t_item("minecraft:shield")],
       [r_item("minecraft:iron_ingot", 8)],
       title="Steel Before Sorcery", sub="Gear up", icon="minecraft:iron_sword",
       desc=["Cursed energy runs dry. A good blade doesn't.",
             "",
             "Technique hits are about as strong as a sword, so you'll still be doing most of your fighting the old way."])
c.side("backpack", [t_item("sophisticatedbackpacks:backpack")], [r_xp(10)],
       title="Pack Light, Pack Lots", desc=["A backpack makes the long trips ahead much easier. Upgrade it later."])
c.side("cooking_pot", [t_item("farmersdelight:cooking_pot")], [r_item("minecraft:carrot", 8), r_item("minecraft:potato", 8)],
       title="Hot Meals", desc=["Farmer's Delight meals give long-lasting buffs. Fights get long."])
c.main("leak", [t_kill("minecraft:zombie", 10), t_kill("minecraft:skeleton", 5)], [r_grade(75), r_item("minecraft:arrow", 32)],
       title="What Leaks Through", sub="The dead walk more often now", icon="minecraft:rotten_flesh",
       desc=["The crack is leaking. Curses drift up through it and settle into the dead, and the nights are worse than they used to be.",
             "",
             "Every hostile mob you put down gives &bgrade XP&r. That's how you get stronger."])
c.side("waystone", [t_item("waystones:waystone")], [r_item("minecraft:ender_pearl", 4)],
       title="Waystones", desc=["Place waystones as you explore so you can always get home. You will be travelling a lot."])
c.side("sleep", [t_item("comforts:sleeping_bag_white")], [r_xp(10)],
       title="Camp Out", desc=["A sleeping bag lets you skip the night without moving your spawn."])
c.main("compass", [t_item("explorerscompass:explorerscompass")], [r_grade(50), r_item("minecraft:cooked_beef", 16)],
       title="Where the Old Sorcerers Went", sub="Chapter complete", icon="explorerscompass:explorerscompass", shape="hexagon", size=1.5,
       desc=["The sorcerers who made the seal left ruins all over the world, and the Calamity's pieces are drawn to them.",
             "",
             "An &eExplorer's Compass&r can point you at any structure. You'll need it to find what comes next."])
done(c)

# =========================================================================
# Chapter 2 - Grades
# =========================================================================
c = new_chapter("2_grades", "II. Climbing the Grades", "Get stronger", "minecraft:iron_sword")
c.main("intro", [t_check()], [r_grade(25)],
       title="Grade 2 Is Not Enough", icon="minecraft:iron_sword", shape="hexagon", size=1.5,
       desc=["Sorcerers are ranked by grade. Right now you're &7Grade 2&r: two abilities and a shallow pool of energy.",
             "",
             "Nobody seals a Calamity at Grade 2. Time to climb."])
c.main("iron_armor", [t_item("minecraft:iron_chestplate"), t_item("minecraft:iron_leggings")], [r_item("minecraft:iron_ingot", 8)],
       title="Armor Up", icon="minecraft:iron_chestplate",
       desc=["Armor reduces technique damage too. Wear a full set before you go looking for trouble."])
c.main("diamonds", [t_item("minecraft:diamond", 5)], [r_item("minecraft:experience_bottle", 8)],
       title="Harder Than Curses", icon="minecraft:diamond",
       desc=["Diamond gear keeps you alive long enough to learn."])
c.side("reforging", [t_item("apotheosis:reforging_table")], [r_item("minecraft:diamond", 2)],
       title="Reforge", desc=["Apotheosis gear rolls random affixes. A Reforging Table lets you reroll them into something good."])
c.main("enchanting", [t_item("minecraft:diamond_pickaxe"), t_item("minecraft:enchanting_table")], [r_item("minecraft:lapis_lazuli", 16)],
       title="Enchanting", icon="minecraft:enchanting_table",
       desc=["A diamond pickaxe mines obsidian. Obsidian builds an enchanting table, and enchanted gear is how you'll survive what comes next."])
c.main("black_flash", [t_adv("cursedtech:black_flash")], [r_grade(75), r_item("minecraft:diamond", 2)],
       title="Black Flash", sub="Space bends with a perfect hit", icon="minecraft:black_dye",
       desc=["Hit something with a &efully charged&r melee attack. Sometimes it becomes a &cBlack Flash&r: about 1.8x damage and a flash that warps the screen.",
             "",
             "Land one and you're &cin the zone&r for 10 seconds, with much better odds. Higher grades require several."])
c.side("night_patrol", [t_kill("minecraft:creeper", 10), t_kill("minecraft:spider", 10), t_kill("minecraft:enderman", 5)],
       [r_grade(150)], title="Night Patrol", icon="minecraft:bow",
       desc=["Extra grade XP for anyone willing to stay out after dark."])
c.side("megatorch", [t_item("torchmaster:megatorch")], [r_xp(20)],
       title="Safe Ground", desc=["A Megatorch stops hostile spawns in a huge radius. Your base deserves a quiet night."])
c.main("obsidian", [t_item("minecraft:obsidian", 10), t_item("minecraft:flint_and_steel")], [r_xp(20)],
       title="A Door Downward", icon="minecraft:flint_and_steel",
       desc=["Ten obsidian and a flint and steel make a Nether portal."])
c.main("nether", [t_dim("minecraft:the_nether")], [r_grade(100)],
       title="Into the Nether", icon="minecraft:obsidian",
       desc=["Curses run thick in the Nether. So does the XP."])
c.main("blaze", [t_kill("minecraft:blaze", 5), t_item("minecraft:blaze_rod", 6)], [r_grade(150)],
       title="Blaze Rods", icon="minecraft:blaze_rod",
       desc=["Find a Nether fortress and hunt blazes. You'll need their rods for brewing now, and to reach the End much later."])
c.main("semi_grade_1", [t_adv("cursedtech:semi_grade_1")], [r_item("minecraft:golden_apple", 2), r_item("minecraft:diamond", 4)],
       title="Semi-Grade 1", sub="Chapter complete: 2,500 grade XP", icon="minecraft:golden_sword", shape="hexagon", size=1.5,
       desc=["Your reserves deepen: more energy, faster regen, harder hits.",
             "",
             "You're strong enough now to start studying how the seal actually worked."])
done(c)

# =========================================================================
# Chapter 3 - Magic
# =========================================================================
c = new_chapter("3_arcane", "III. Arcane Studies", "How the seal was made", "ars_nouveau:novice_spell_book")
c.main("intro", [t_check()], [r_xp(20)],
       title="Notes in the Ruins", icon="minecraft:writable_book", shape="hexagon", size=1.5,
       desc=["In the ruins you find what's left of the old sorcerers' notes. Cursed energy alone never held the Calamity. They wove it together with every other kind of magic they knew.",
             "",
             "To rebuild the seal, you'll have to learn those arts too."])
c.main("notebook", [t_item("ars_nouveau:worn_notebook")], [r_xp(20)],
       title="A Worn Notebook", icon="ars_nouveau:worn_notebook",
       desc=["Ars Nouveau's guidebook. Everything about source and glyphs is inside."])
c.main("imbuement", [t_item("ars_nouveau:imbuement_chamber")], [r_item("minecraft:amethyst_shard", 16)],
       title="Imbuement Chamber", icon="ars_nouveau:imbuement_chamber",
       desc=["The chamber soaks items in source. Put amethyst in it to make Source Gems."])
c.main("source_gem", [t_item("ars_nouveau:source_gem", 8)], [r_xp(20)],
       title="Source Gems", icon="ars_nouveau:source_gem",
       desc=["The basic currency of Ars Nouveau. Almost every recipe from here on uses them."])
c.main("source_jar", [t_item("ars_nouveau:source_jar")], [r_xp(20)],
       title="Store Source", icon="ars_nouveau:source_jar",
       desc=["Source jars hold the source your machines run on. Fill one with a Sourcelink or by hand."])
c.main("spell_book", [t_item("ars_nouveau:novice_spell_book"), t_item("ars_nouveau:scribes_table")], [r_item("ars_nouveau:source_gem", 4)],
       title="First Spells", icon="ars_nouveau:novice_spell_book",
       desc=["Write your own spells from glyphs, and unlock new glyphs at the Scribe's Table. Magic and cursed techniques stack: use both."])
c.main("pedestals", [t_item("ars_nouveau:arcane_pedestal", 4)], [r_xp(30)],
       title="Pedestals", icon="ars_nouveau:arcane_pedestal",
       desc=["Four pedestals to hold ingredients around a core."])
c.side("apprentice", [t_item("ars_nouveau:apprentice_spell_book")], [r_xp(30)],
       title="Apprentice Spell Book", desc=["More spell slots, stronger glyphs."])
c.side("irons", [t_item("irons_spellbooks:inscription_table")], [r_item("irons_spellbooks:arcane_essence", 8)],
       title="A Different School", desc=["Iron's Spells 'n Spellbooks has dozens of ready-made spells and some excellent wizard armor."])
c.main("apparatus", [t_item("ars_nouveau:arcane_core"), t_item("ars_nouveau:enchanting_apparatus")], [r_grade(150)],
       title="The Apparatus", sub="Chapter complete", icon="ars_nouveau:enchanting_apparatus", shape="hexagon", size=1.5,
       desc=["The notes describe crafting on a ring of pedestals around a central core. The Enchanting Apparatus works the same way.",
             "",
             "The real seal needs something far bigger, and far more power than magic alone can give."])
c.side("malum", [t_item("malum:spirit_altar")], [r_xp(30)],
       title="Spirit Arcana", desc=["Malum harvests the spirits of what you kill and infuses them into gear. Useful for an exorcist."])
c.side("occultism", [t_item("occultism:dictionary_of_spirits")], [r_xp(30)],
       title="Bound Spirits", desc=["Occultism lets you summon and bind spirits to work for you, including miners that dig ore while you're away."])
done(c)

# =========================================================================
# Chapter 4 - Technology
# =========================================================================
c = new_chapter("4_engines", "IV. Engines of the Modern Age", "Power for the ritual", "mekanism:metallurgic_infuser")
c.main("intro", [t_check()], [r_xp(20)],
       title="What They Didn't Have", icon="minecraft:redstone", shape="hexagon", size=1.5,
       desc=["The old sorcerers needed a hundred of them pouring their lives into one ritual.",
             "",
             "You have machines. The seal you're going to build needs a lot of power, so start an industry."])
c.main("andesite", [t_item("create:andesite_alloy", 16)], [r_item("create:cogwheel", 8)],
       title="Andesite Alloy", icon="create:andesite_alloy",
       desc=["Andesite and iron nuggets. The building block of everything in Create."])
c.main("water_wheel", [t_item("create:water_wheel"), t_item("create:shaft", 8)], [r_item("create:cogwheel", 8)],
       title="Turning Gears", icon="create:water_wheel",
       desc=["Create runs on rotation. A water wheel in flowing water turns shafts, and shafts turn machines."])
c.main("press", [t_item("create:mechanical_press")], [r_xp(30)],
       title="Mechanical Press", icon="create:mechanical_press",
       desc=["Presses turn ingots into sheets. You'll need sheets for Create's better machines."])
c.side("brass", [t_item("create:brass_ingot", 8)], [r_xp(30)],
       title="Brass", desc=["Brass opens up Create's automation: deployers, arms and logistics."])
c.main("osmium", [t_item("mekanism:ingot_osmium", 8)], [r_item("minecraft:coal", 16)],
       title="Osmium", icon="mekanism:ingot_osmium",
       desc=["Osmium ore is Mekanism's starting metal. Smelt the raw ore."])
c.main("infuser", [t_item("mekanism:metallurgic_infuser")], [r_xp(30)],
       title="Metallurgic Infuser", icon="mekanism:metallurgic_infuser",
       desc=["Infuses metals with carbon, redstone and more. Power it with a generator, or with Create rotation through an Alternator from Create Crafts & Additions."])
c.main("steel", [t_item("mekanism:ingot_steel", 8), t_item("mekanism:steel_casing")], [r_item("mekanism:ingot_osmium", 8)],
       title="Steel Casing", icon="mekanism:steel_casing",
       desc=["Steel, and the casing every Mekanism machine is built around."])
c.main("ore_processing", [t_item("mekanism:enrichment_chamber")], [r_xp(40)],
       title="Double Your Ore", icon="mekanism:enrichment_chamber",
       desc=["Ore processing doubles everything you mine. You'll need a mountain of metal."])
c.side("powah", [t_item("powah:energizing_orb")], [r_xp(30)],
       title="Powah", desc=["Powah's generators and energy cells are a simple way to make a lot of power."])
c.side("ae2", [t_item("ae2:controller")], [r_xp(50)],
       title="Digital Storage", desc=["Applied Energistics 2 turns your chests into one searchable network. Your stockpile is about to get big."])
c.main("circuits", [t_item("mekanism:basic_control_circuit", 4)], [r_xp(30)],
       title="Control Circuits", icon="mekanism:basic_control_circuit",
       desc=["Osmium and redstone in the infuser. Every upgrade tier needs circuits."])
c.main("generator", [t_item("mekanismgenerators:heat_generator")], [r_xp(30)],
       title="Generate Power", icon="mekanismgenerators:heat_generator",
       desc=["A Heat Generator burns fuel or sits next to lava. Steady power to start with."])
c.main("battery", [t_item("mekanism:basic_energy_cube")], [r_grade(150)],
       title="Stored Lightning", sub="Chapter complete", icon="mekanism:basic_energy_cube", shape="hexagon", size=1.5,
       desc=["Power, stored and ready. Now you need the strength to survive what the Calamity will throw at you."])
done(c)

# =========================================================================
# Chapter 5 - Grade 1 and Domains
# =========================================================================
c = new_chapter("5_domain", "V. A World of Your Own", "Grade 1 and Domain Expansion", "minecraft:obsidian")
c.main("intro", [t_check()], [r_grade(50)],
       title="The Wardens Stir", icon="minecraft:iron_axe", shape="hexagon", size=1.5,
       desc=["Things are getting worse. Old guardians have woken up across the world, twisted by curse energy from the crack.",
             "",
             "Put them down. Every boss you kill gives a huge pile of grade XP and counts toward Special Grade."])
c.main("wroughtnaut", [t_kill("mowziesmobs:ferrous_wroughtnaut")], [r_grade(200), r_item("minecraft:diamond", 3)],
       title="Ferrous Wroughtnaut", sub="The armored guardian", icon="minecraft:iron_axe",
       desc=["It sleeps in underground halls. Hit it from behind when it gets stuck after a swing."])
c.side("frostmaw", [t_kill("mowziesmobs:frostmaw")], [r_grade(200)], title="Frostmaw", icon="minecraft:blue_ice",
       desc=["A giant of the snowy biomes."])
c.side("umvuthi", [t_kill("mowziesmobs:umvuthi")], [r_grade(200)], title="Umvuthi", icon="minecraft:gold_block",
       desc=["The sun-masked king of the savanna."])
c.main("grade_1", [t_adv("cursedtech:grade_1")], [r_item("minecraft:totem_of_undying"), r_item("minecraft:diamond", 6)],
       title="Grade 1", sub="8,000 XP and 3 Black Flashes", icon="minecraft:diamond_sword",
       desc=["You're now one of the strongest sorcerers alive. And you've unlocked something new."])
c.main("domain", [t_adv("cursedtech:domain")], [r_grade(100)],
       title="Domain Expansion", sub="Press V", icon="minecraft:obsidian",
       desc=["A domain raises a barrier around you, and everything inside suffers your technique's sure-hit effect.",
             "",
             "Two overlapping domains &6clash&r and the stronger one wins. Afterwards your technique &cburns out&r for a few seconds, so pick your moment."])
c.side("sculptor", [t_kill("mowziesmobs:sculptor")], [r_grade(200)], title="The Sculptor", icon="minecraft:chiseled_stone_bricks",
       desc=["A climbing challenge at the top of a stone pillar."])
c.main("netherite", [t_item("minecraft:netherite_ingot")], [r_item("minecraft:netherite_scrap", 2)],
       title="Netherite", icon="minecraft:netherite_ingot",
       desc=["Ancient debris lies deep in the Nether. Upgrade your best gear before the next fight."])
c.main("skulls", [t_item("minecraft:wither_skeleton_skull", 3), t_item("minecraft:soul_sand", 4)], [r_xp(50)],
       title="Three Skulls", icon="minecraft:wither_skeleton_skull",
       desc=["Wither skeletons in Nether fortresses drop their skulls, rarely. You need three."])
c.main("wither", [t_kill("minecraft:wither")], [r_grade(250), r_item("minecraft:netherite_ingot")],
       title="The Wither", sub="Chapter complete", icon="minecraft:wither_skeleton_skull", shape="hexagon", size=1.5,
       desc=["Fight it somewhere you don't mind wrecking. Trap it in your domain.",
             "",
             "When it dies, something answers from far away: a sound like a heartbeat from every direction at once."])
done(c)

# =========================================================================
# Chapter 6 - Cataclysm bosses
# =========================================================================
c = new_chapter("6_fragments", "VI. Fragments of the Calamity", "Special Grade", "cataclysm:ignitium_ingot")
c.main("intro", [t_check()], [r_grade(50)],
       title="Fragments", icon="minecraft:netherite_scrap", shape="hexagon", size=1.5,
       desc=["Now you know what that heartbeat was. The great beasts sleeping in the deepest ruins aren't natural. Each one is a &5fragment of the Calamity&r that slipped through the crack.",
             "",
             "Kill them, and the Calamity can't rebuild itself. Each fragment leaves behind cursed metal, and you'll need that metal later."])
c.main("eyes", [t_item("minecraft:ender_eye", 12)], [r_item("minecraft:ender_pearl", 8)],
       title="Eyes of Ender", icon="minecraft:ender_eye",
       desc=["Blaze powder and ender pearls. Throw one and follow it to a stronghold."])
c.main("end", [t_dim("minecraft:the_end"), t_kill("minecraft:ender_dragon")], [r_grade(300), r_item("minecraft:elytra")],
       title="Beyond the Portal", icon="minecraft:dragon_head",
       desc=["The Ender Dragon has been guarding one of the old seal-stones all this time. Free the End. The Chaos Guardian is waiting there too, but not yet."])
c.side("ender_guardian", [t_kill("cataclysm:ender_guardian")], [r_grade(300)],
       title="Ender Guardian", icon="cataclysm:gauntlet_of_guard",
       desc=["A fragment that hides in a fortress on the End islands."])
c.main("monstrosity", [t_kill("cataclysm:netherite_monstrosity")], [r_grade(300), r_item("minecraft:netherite_ingot", 2)],
       title="Netherite Monstrosity", icon="minecraft:netherite_block",
       desc=["Sleeping in a soul-black fortress in the Nether. It hits like a landslide. Fire resistance helps."])
c.main("ignis", [t_kill("cataclysm:ignis"), t_item("cataclysm:ignitium_ingot")], [r_grade(400)],
       title="Ignis", sub="The burning knight", icon="cataclysm:ignitium_ingot",
       desc=["Its fortress burns in the Nether. Ignitium is the first of the cursed metals you need."])
c.side("leviathan", [t_kill("cataclysm:the_leviathan")], [r_grade(400)],
       title="The Leviathan", icon="cataclysm:tidal_claws",
       desc=["A fragment that drowned itself in a sunken city."])
c.side("remnant", [t_kill("cataclysm:ancient_remnant")], [r_grade(400)],
       title="Ancient Remnant", icon="cataclysm:ancient_metal_ingot",
       desc=["Buried under the desert sands."])
c.main("harbinger", [t_kill("cataclysm:the_harbinger"), t_item("cataclysm:witherite_ingot")], [r_grade(400)],
       title="The Harbinger", sub="The machine that heralds it", icon="cataclysm:witherite_ingot",
       desc=["A war machine in a hidden factory, built to call the Calamity home. Witherite is the second cursed metal."])
c.side("maledictus", [t_kill("cataclysm:maledictus")], [r_grade(400)],
       title="Maledictus", icon="cataclysm:cursium_ingot",
       desc=["A reaper of souls in a frozen citadel. Not one of the fragments, but it fights like one, and Cursium makes excellent gear."])
c.main("special", [t_adv("cursedtech:special")], [r_item("minecraft:nether_star"), r_item("minecraft:netherite_ingot", 2)],
       title="Special Grade", sub="Chapter complete", icon="minecraft:netherite_sword", shape="hexagon", size=1.5,
       desc=["30,000 XP, 12 Black Flashes, 2 bosses. You've reached the peak.",
             "",
             "You unlock your &cMaximum&r technique (G) and &aReverse Cursed Technique&r, which slowly heals you with cursed energy.",
             "",
             "You're as strong as the sorcerers who made the first seal. Now build a better one."])
c.side("maximum", [t_adv("cursedtech:maximum")], [r_grade(100)], title="Maximum", icon="minecraft:nether_star", shape="gear",
       desc=["Unleash everything you have."])
done(c)

# =========================================================================
# Chapter 7 - Draconic Evolution
# =========================================================================
c = new_chapter("7_forging", "VII. Forging the Seal", "Draconic fusion", "draconicevolution:chaotic_core")
c.main("intro", [t_check()], [r_xp(30)],
       title="A Better Seal", icon="draconicevolution:draconium_core", shape="hexagon", size=1.5,
       desc=["The old seal was stone and sacrifice. Yours will be &ddraconic&r: forged from dragon-touched metal, fused with power, and set around a heart of pure chaos.",
             "",
             "The path runs Draconium, Wyvern, Awakened, Chaotic. The last core is the seal itself."])
c.main("draconium", [t_item("draconicevolution:draconium_ingot", 16)], [r_item("draconicevolution:draconium_ingot", 8)],
       title="Draconium", icon="draconicevolution:draconium_ingot",
       desc=["Draconium ore is found deep in the Overworld, and more plentifully in the Nether and End. It's tough to mine without at least a diamond pick."])
c.main("fusion", [t_item("draconicevolution:draconium_core"), t_item("draconicevolution:crafting_core"), t_item("draconicevolution:basic_crafting_injector", 4)],
       [r_grade(100)],
       title="Fusion Crafting", icon="draconicevolution:crafting_core",
       desc=["A Fusion Crafting Core surrounded by injectors, just like the Apparatus but much stronger. Every core from here on is fused, and fusion eats power."])
c.side("energy_core", [t_item("draconicevolution:energy_core")], [r_xp(50)],
       title="Energy Core", desc=["A multiblock battery that holds staggering amounts of power. Fusion crafting will drain your basic cells fast."])
c.main("wyvern", [t_item("draconicevolution:wyvern_core")], [r_grade(150)],
       title="Wyvern Core", icon="draconicevolution:wyvern_core",
       desc=["The second tier. Wyvern tools and armor are a big step up from netherite."])
c.main("heart", [t_item("draconicevolution:dragon_heart")], [r_grade(150)],
       title="A Dragon's Heart", icon="draconicevolution:dragon_heart",
       desc=["Draconium needs to be &eawakened&r with the heart of a dragon. Kill the Ender Dragon again (you can respawn it) and claim its heart."])
c.main("awakened", [t_item("draconicevolution:awakened_draconium_ingot", 4), t_item("draconicevolution:awakened_core")], [r_grade(200)],
       title="Awakened", icon="draconicevolution:awakened_core",
       desc=["Awakened draconium, fused with cursed metal. The seal is nearly ready. It only needs a heart."])
c.side("cursed_metal", [t_item("cataclysm:ignitium_ingot", 4), t_item("cataclysm:witherite_ingot", 4)], [r_grade(150)],
       title="Temper with Cursed Metal", icon="cataclysm:ignitium_ingot",
       desc=["Gear made from the fragments' metal is some of the best in the pack. You'll want it for the last fights."])
c.main("chaos_guardian", [t_kill("draconicevolution:draconic_guardian"), t_item("draconicevolution:chaos_shard", 4)],
       [r_grade(500)],
       title="The Chaos Guardian", sub="The hardest fight before the last", icon="draconicevolution:chaos_shard",
       desc=["On a distant island in the End lives the Chaos Guardian, a dragon fed on raw chaos. Its shards are the only thing strong enough to anchor your seal.",
             "",
             "Bring Wyvern gear at minimum, and friends. Destroy its crystals first."])
c.main("chaotic_core", [t_item("draconicevolution:chaotic_core")], [r_grade(300)],
       title="The Seal", sub="Chapter complete", icon="draconicevolution:chaotic_core", shape="hexagon", size=2.0,
       desc=["A Chaotic Core: draconium, cursed energy and chaos, fused into something nothing can break.",
             "",
             "This is your seal. Keep it close. The Calamity knows you've made it, and it's coming."])
done(c)

# =========================================================================
# Chapter 8 - Finale
# =========================================================================
c = new_chapter("8_finale", "VIII. Seal the Calamity", "The end goal", "cursedtech:calamity_heart")
c.main("intro", [t_check()], [],
       title="The Name Under the Stone", icon="minecraft:soul_lantern", shape="hexagon", size=1.5,
       desc=["The last of the old notes finally makes sense. The Calamity was never a beast. It was a &5sorcerer&r, the strongest who ever lived, so strong the others could only bury him alive.",
             "",
             "The fragments you killed were pieces of his power that leaked out through the crack. With them gone, he's alone down there, and weaker than he has been in a thousand years.",
             "",
             "The old sorcerers sealed him in his sleep. You're going to wake him, beat him, and seal him for good."])
c.main("altar", [t_item("cursedtech:sealing_altar")], [r_xp(50)],
       title="The Sealing Altar", icon="cursedtech:sealing_altar",
       desc=["Build a Sealing Altar: amethyst, crying obsidian, obsidian and a Nether Star.",
             "",
             "Place it somewhere with room to fight, away from anything you care about. He doesn't break blocks, but he hits very hard."])
c.main("prepare", [t_item("minecraft:totem_of_undying"), t_item("minecraft:enchanted_golden_apple")], [r_item("minecraft:golden_apple", 4)],
       title="Last Preparations", icon="minecraft:totem_of_undying",
       desc=["Bring a totem, food and friends.",
             "",
             "What to expect: every attack is telegraphed. A &5purple line&r means a cut is coming, and a &5purple ring&r means get out. At half health he opens his own &5domain&r. Open yours inside it and his sure-hit can't touch you. When his domain ends he &cburns out&r and takes extra damage, so that's your window."])
c.main("calamity", [t_kill("cursedtech:calamity"), t_item("cursedtech:calamity_heart")], [r_grade(1000)],
       title="The Calamity", sub="Use the seal on the altar", icon="cursedtech:calamity_heart", shape="gear", size=2.0,
       desc=["Hold your Chaotic Core and use it on the altar. The seal isn't used up.",
             "",
             "He rises. Win.",
             "",
             "When he falls he leaves his &5Heart&r behind: everything he was, in a form small enough to bind."])
c.main("sealed", [t_item("draconicevolution:chaotic_core"), t_item("cursedtech:calamity_heart")],
       [r_item("minecraft:nether_star", 2), r_item("minecraft:beacon"), r_xp(500),
        r_cmd('/tellraw @a ["",{"text":"[Cursed Arts] ","color":"dark_purple"},{"selector":"{p}"},{"text":" has sealed the Calamity.","color":"light_purple"}]')],
       title="Seal the Calamity", sub="The end", icon="draconicevolution:chaotic_core", shape="hexagon", size=2.5,
       desc=["Hold the seal in one hand and his heart in the other.",
             "",
             "Cursed energy, magic, machines and chaos, bound together the way the old sorcerers never could. The crack closes. The nights go quiet.",
             "",
             "It's over. Thank you for playing &dCursed Arts&r.",
             "",
             "&7The altar still works if you want a rematch, and every boss still drops loot."])
done(c)

# -------------------------------------------------------------------- write
qdir = OUT
if os.path.isdir(f"{qdir}/chapters"):
    shutil.rmtree(f"{qdir}/chapters")
os.makedirs(f"{qdir}/chapters")
os.makedirs(f"{qdir}/lang", exist_ok=True)
for name, body in CHAPTERS:
    open(f"{qdir}/chapters/{name}.snbt", "w").write(body)
LANG["file.0000000000000001.title"] = "Cursed Arts: Seal the Calamity"
with open(f"{qdir}/lang/en_us.snbt", "w") as f:
    f.write("{\n")
    for k in sorted(LANG):
        v = LANG[k]
        if isinstance(v, list):
            f.write("\t%s: [%s]\n" % (k, ", ".join(s(x) for x in v)))
        else:
            f.write("\t%s: %s\n" % (k, s(v)))
    f.write("}\n")
open(f"{qdir}/data.snbt", "w").write("""{
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
	progression_mode: "linear"
	show_lock_icons: true
	verify_on_load: false
	version: 13
}
""")
open(f"{qdir}/chapter_groups.snbt", "w").write("{\n\tchapter_groups: [ ]\n}\n")
nq = sum(b.count("\t\t\tid: ") for _, b in CHAPTERS)
nopt = sum(b.count("optional: true") for _, b in CHAPTERS)
print(f"{len(CHAPTERS)} chapters, {nq} quests ({nopt} optional), {len(LANG)} lang entries")
