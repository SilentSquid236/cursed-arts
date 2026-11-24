# Cursed Arts

A NeoForge 1.21.1 modpack built around **[Cursed Techniques](https://github.com/SilentSquid236/cursed-techniques)**: *Jujutsu Kaisen*-style cursed techniques, Domain Expansions and Black Flash, surrounded by spell magic, modern tech and a cinematic visual stack.

## What's inside

**Magic**: Cursed Techniques · Iron's Spells 'n Spellbooks · Ars Nouveau · Occultism

**Modern tech**: Create · Mekanism (+ Generators, Tools) · Applied Energistics 2 · Immersive Engineering

**Combat & bosses**: Better Combat · L_Ender's Cataclysm · Mowzie's Mobs

**Visuals & sound** (client): Sodium · Iris · Complementary Unbound / Reimagined & BSL shaders · Particle Rain · Not Enough Animations · Sound Physics Remastered · AmbientSounds · ImmediatelyFast

**Quality of life**: JEI · Jade · Xaero's Minimap & World Map · Waystones · Sophisticated Backpacks · AppleSkin · Mouse Tweaks · Controlling

**Performance**: ModernFix · FerriteCore · Lithium

Plus their libraries (GeckoLib, Curios, Balm, playerAnimator, ...). The full, exact list is in [`mods/`](mods).

## Installing

Grab the latest file from [Releases](../../releases):

- **CurseForge app**: `Cursed-Arts-<version>.zip` → *Create Custom Profile → Import*.
- **Prism Launcher / Modrinth App**: `Cursed-Arts-<version>.mrpack` → *Add Instance → Import*.

Give the game at least **6 GB** of RAM. To turn on shaders: *Options → Video Settings → Shader Packs* (or press `K`), then pick Complementary Unbound.

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

To publish, bump `version` in `pack.toml`, run `packwiz refresh`, and push to `main`. GitHub Actions exports the CurseForge `.zip` and Modrinth `.mrpack`, creates the release, and uploads to CurseForge once `CURSEFORGE_TOKEN` and `CURSEFORGE_PROJECT_ID` are configured (see `.github/workflows/release.yml`).

## License

The pack configuration is MIT. Each included mod keeps its own license; mods are downloaded from their official pages, not redistributed here, except Cursed Techniques (MIT), which is bundled until it is live on CurseForge.
