# Free Assets & Open-Source Sources

Catalog of assets and code that are free to use in MyDroidDeck. Licenses were
checked against the linked sources; **verify the license at the source before use**
and keep an attribution/license note (see `AGENTS.md`). Permissive licenses
(CC0, MIT, ISC, Apache-2.0, BSD, OFL) are preferred.

## Icons
| Source | License | Notes |
| --- | --- | --- |
| [Material Symbols / Material Icons](https://github.com/google/material-design-icons) | Apache-2.0 | Google's official set (~2,500+); works well with a Material Android UI. |
| [Lucide](https://github.com/lucide-icons/lucide) | ISC (Feather-derived parts MIT) | 1,600+ clean SVG icons; official Android/Compose-friendly packages. |
| [Tabler Icons](https://github.com/tabler/tabler-icons) | MIT | 6,200+ SVG icons, 24px grid. |
| [Phosphor Icons](https://github.com/phosphor-icons/core) | MIT | Multiple weights (thin → fill). |
| [Heroicons](https://github.com/tailwindlabs/heroicons) | MIT | Outline + solid. |
| [Bootstrap Icons](https://github.com/twbs/icons) | MIT | Large general set. |
| [Feather](https://github.com/feathericons/feather) | MIT | Minimal line icons. |
| [Simple Icons](https://github.com/simple-icons/simple-icons) | CC0 | **Brand logos** — trademark rules still apply. |
| [Font Awesome Free](https://github.com/FortAwesome/Font-Awesome) | Icons CC BY 4.0; fonts SIL OFL 1.1; code MIT | Attribution required for icons. |
| [Iconify](https://iconify.design/) | Aggregator | Unified API/CLI over many of the sets above. |

## Fonts
| Source | License | Notes |
| --- | --- | --- |
| [Google Fonts](https://fonts.google.com/) | Mostly SIL OFL 1.1 (some Apache-2.0/UFL) | Free for commercial use and embedding; Android-friendly. |
| [Font Squirrel](https://www.fontsquirrel.com/) | Mixed (filter to 100% free) | Curated free fonts. |
| Inter, Roboto, Noto, JetBrains Mono, Fira Code | OFL / Apache-2.0 | Common UI/mono choices; Noto has broad script coverage. |

## Illustrations & UI kits
| Source | License | Notes |
| --- | --- | --- |
| [unDraw](https://undraw.co/license) | Custom "open" license | Free commercial use, no attribution; **no AI training, no redistribution as packs, no competing service**. |
| [Open Peeps](https://www.openpeeps.com/) | CC0 | Hand-drawn mix-and-match people. |
| [Open Doodles](https://www.opendoodles.com/) | CC0 | Sketchy illustrations. |
| [Humaaans](https://www.humaaans.com/) | CC0 | Mix-and-match characters (verify current terms). |
| [Material 3 Design Kit (Figma)](https://www.figma.com/community/file/1035203688168086460) | Free | Google's official Material 3 components. |
| [Figma Community](https://www.figma.com/community) | Per-author | Many free UI kits; check each file's license. |

## 3D, textures & backgrounds
| Source | License | Notes |
| --- | --- | --- |
| [Poly Haven](https://polyhaven.com/license) | CC0 | HDRIs, PBR textures, 3D models. |
| [ambientCG](https://ambientCG.com/) | CC0 | 2,000+ PBR materials, HDRIs, models. |
| [Kenney](https://kenney.nl/) | CC0 | UI packs, sprites, 3D kits, audio. |
| [OpenGameArt](https://opengameart.org/) | Varies (CC0/CC-BY/CC-BY-SA/GPL) | Check each asset — some require attribution/share-alike. |

## Audio
| Source | License | Notes |
| --- | --- | --- |
| [Kenney Audio](https://kenney.nl/assets/category:Audio) | CC0 | UI/interface + impact sound effects (ideal for button feedback). |
| [Freesound](https://freesound.org/) | Varies (CC0 / CC-BY / CC-BY-NC) | Filter by license; NC is **not** usable in commercial products. |
| [cc0-sounds](https://cc0-sounds.netlify.app/) | CC0 | Mirrors CC0 packs (incl. Kenney). |

## Photos (weaker than permissive — read terms)
| Source | License | Notes |
| --- | --- | --- |
| [Unsplash](https://unsplash.com/license) | Unsplash License | Free incl. commercial; **no selling unaltered copies / competing service**. |
| [Pexels](https://www.pexels.com/license/) | Pexels License | Free incl. commercial; similar restrictions. |

## Open-source code & libraries
### Android (`app/`)
| Library | License | Use |
| --- | --- | --- |
| [AndroidX](https://github.com/androidx/androidx) | Apache-2.0 | Core Android/Kotlin support. |
| [Material Components for Android](https://github.com/material-components/material-components-android) | Apache-2.0 | Material design widgets. |
| [Retrofit](https://github.com/square/retrofit) | Apache-2.0 | Type-safe HTTP client. |
| [OkHttp](https://github.com/square/okhttp) | Apache-2.0 | HTTP/WebSocket transport. |
| [Moshi](https://github.com/square/moshi) / [Gson](https://github.com/google/gson) | Apache-2.0 | JSON. |
| [Room](https://developer.android.com/training/data-storage/room) | Apache-2.0 | Local database. |
| [Coil](https://github.com/coil-kt/coil) / [Glide](https://github.com/bumptech/glide) | Apache-2.0 | Image loading. |
| [Hilt/Dagger](https://github.com/google/dagger) | Apache-2.0 | Dependency injection. |
| [Java-WebSocket](https://github.com/TooTallNate/Java-WebSocket) | MIT | WebSocket client if not using OkHttp. |
| [LeakCanary](https://github.com/square/leakcanary) / [Timber](https://github.com/JakeWharton/timber) | Apache-2.0 | Debug/logging (dev only). |
| [ZXing Android Embedded](https://github.com/journeyapps/zxing-android-embedded) (wraps [ZXing core](https://github.com/zxing/zxing)) | Apache-2.0 | Camera + QR scanning for first-run pairing; bundled, no Play Services. |

### Server (`server/`)
| Library | License | Use |
| --- | --- | --- |
| [NestJS](https://github.com/nestjs/nest) | MIT | Structured TypeScript backend. |
| [Fastify](https://github.com/fastify/fastify) / [Express](https://github.com/expressjs/express) | MIT | HTTP servers (Nest can use either). |
| [Prisma](https://github.com/prisma/prisma) / [Drizzle](https://github.com/drizzle-team/drizzle-orm) / [TypeORM](https://github.com/typeorm/typeorm) | Apache-2.0 / Apache-2.0 / MIT | Database ORMs. |
| [Socket.IO](https://github.com/socketio/socket.io) / [ws](https://github.com/websockets/ws) | MIT | Real-time control channel. |
| [Zod](https://github.com/colinhacks/zod) | MIT | Runtime validation. |
| [Vitest](https://github.com/vitest-dev/vitest) / [Jest](https://github.com/jestjs/jest) | MIT | Testing. |
| [React](https://github.com/facebook/react) | MIT | Admin UI. |
| [Segno](https://github.com/heuer/segno) | BSD-3-Clause | Pure-Python QR code renderer (pairing PNG in the admin UI; no native deps). |
| [Pillow](https://github.com/python-pillow/Pillow) / [zxing-cpp](https://github.com/zxing-cpp/zxing-cpp) | MIT-CMU (HPND) / Apache-2.0 | **Test-only** decoders proving the pairing QR reads back. |

### Homonymous / related projects (reference only — verify each license)
- [sDeck](https://github.com/itsiurisilva/sDeck) — MIT, self-hosted web Stream Deck.
- [ODeck](https://github.com/willianrod/ODeck) — MIT, Electron + React + socket.io + mobile app.
- [TouchDeck](https://github.com/TouchDeck/TouchDeck) — open-source touchscreen deck (check license).
- [Code Deck](https://github.com/hagronnestad/code-deck) — C# cross-platform deck (check license).
- OpenMacroBoard / StreamDeckSharp, Bitfocus Companion, Deckboard, Macro Deck — study for architecture and plugin models.

## Code hosting & discovery
- [GitHub](https://github.com/), [GitLab](https://gitlab.com/), [Codeberg](https://codeberg.org/),
  [Bitbucket](https://bitbucket.org/), [SourceForge](https://sourceforge.net/),
  [Gitee](https://gitee.com/) — browse/fork projects; each repo states its own license.
- Prefer repos with an explicit OSI license (MIT/Apache-2.0/ISC/BSD) for code you copy.
