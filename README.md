# Cursed Arts

A NeoForge 1.21.1 modpack built around **[Cursed Techniques](https://github.com/SilentSquid236/cursed-techniques)**: *Jujutsu Kaisen*-style cursed techniques, Domain Expansions and Black Flash, surrounded by spell magic, modern tech and a cinematic visual stack.

## What's inside

**Magic**: Cursed Techniques · Iron's Spells 'n Spellbooks · Ars Nouveau (+ Ars Elemental, Ars Creo, Ars Additions) · Occultism · Malum · Forbidden & Arcanus · Astral Sorcery · Reliquary · Relics

**Modern tech**: Create (+ Crafts & Additions, Create: Connected) · Mekanism (+ Generators, Tools, Additions) · Applied Energistics 2 (+ MEGA Cells, Applied Mekanistics) · Immersive Engineering · Draconic Evolution · Powah · Industrial Foregoing · PneumaticCraft: Repressurized · Oritech · Flux Networks · Pipez · LaserIO · Iron Jetpacks · Mining Gadgets · Building Gadgets · Just Dire Things

**Farming & gear**: Mystical Agriculture (+ Agradditions) · Silent Gear · Farmer's Delight · Apotheosis

**Combat & bosses**: Better Combat · L_Ender's Cataclysm · Mowzie's Mobs

**World generation & exploration**: Tectonic · Terralith · Oh The Biomes We've Gone · YUNG's Better Mineshafts / Strongholds / Desert Temples / Jungle Temples / Witch Huts / Bridges / Extras · When Dungeons Arise · Dungeon Crawl · Explorer's Compass · Nature's Compass · Lootr

**Building & decoration**: Supplementaries · Handcrafted · Macaw's Furniture · Torchmaster

**Visuals & sound** (client): Sodium · Iris · Complementary Unbound / Reimagined & BSL shaders · Particle Rain · Not Enough Animations · Sound Physics Remastered · AmbientSounds · ImmediatelyFast

**Quality of life**: FTB Ultimine · FTB Teams · FTB Essentials · JEI · Just Enough Resources · Jade · Xaero's Minimap & World Map · Waystones · Sophisticated Backpacks · Tool Belt · Simple Magnets · Crafting Tweaks · TrashSlot · Comforts · Easy Villagers · AppleSkin · Mouse Tweaks · Controlling

**Performance**: ModernFix · FerriteCore · Lithium · Clumps · spark

Many of these are hand-picked from FTB Evolution (1.21.1). Plus their libraries. The full, exact list is in [`mods/`](mods).

## Installing

Grab the latest file from [Releases](../../releases):

Download `Cursed-Arts-<version>.zip`, then:

- **CurseForge app**: *Create Custom Profile → Import* the zip.
- **Prism Launcher**: *Add Instance → Import* the zip. Prism asks you to download one or two mods by hand whose authors block third-party downloads (it opens the pages for you).

Give the game at least **8 GB** of RAM. To turn on shaders: *Options → Video Settings → Shader Packs* (or press `K`), then pick Complementary Unbound.

### Controls

| Key | Action |
|---|---|
| Z / X | Cursed technique abilities |
| V | Domain Expansion |

Magic mods add their own keys. If two clash, *Options → Controls* has a search box (Controlling) and highlights conflicts.

## Server

The server only needs the mods marked `side = "both"` or `"server"`. With the [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) image, point `PACKWIZ_URL` at this repo's `pack.toml` (repo must be public) or install the exported pack.

## Maintaining

The pack is managed with [packwiz](https://packwiz.infra.link/):

```
packwiz curseforge add <slug>   # add a mod (dependencies resolve automatically)
packwiz remove <name>
packwiz update --all
packwiz refresh                 # after any manual edit
```

Mark client-only mods with `side = "client"` in their `.pw.toml`.

To publish, bump `version` in `pack.toml`, run `packwiz refresh`, and push to `main`. GitHub Actions exports the CurseForge `.zip`, creates the release, and uploads to CurseForge once `CURSEFORGE_TOKEN` and `CURSEFORGE_PROJECT_ID` are configured (see `.github/workflows/release.yml`).

## License

The pack configuration is MIT. Each included mod keeps its own license; mods are downloaded from their official pages, not redistributed here, except Cursed Techniques (MIT), which is bundled until it is live on CurseForge.
