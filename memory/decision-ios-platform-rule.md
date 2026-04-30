# Decisión D-IOS-001 — Cliente nativo Apple: iPhone + iPad + Watch, 100% Swift

**Tipo**: decision
**Autor**: Antonio
**Fecha**: 2026-04-30

## Qué

El cliente nativo Apple del backend Training (proyecto Xcode en `/Users/antoniohermoso/IOS/Dobacksoft Training`) tiene **scope estricto y permanente**:

- **Plataformas soportadas:**
  - **iPhone** (foco demo Madrid 11/05).
  - **iPad** (mismo target, layouts adaptativos SwiftUI cuando size class sea regular).
  - **Apple Watch** (target separado, ligero — solo resumen/notificación, no app completa).
- **Plataformas NO soportadas:**
  - macOS (sin Mac Catalyst, sin AppKit, sin nada).
  - visionOS / xrOS / Vision Pro.
  - tvOS, watchOS standalone (Watch siempre dependiente del iPhone).
- **Frameworks permitidos:** Swift + SwiftUI + Apple SDKs únicamente (URLSession, Keychain `Security.framework`, WatchKit, UserNotifications, Combine, async/await, SwiftData si hace falta).
- **Frameworks NO permitidos:** React Native, Flutter, Capacitor, Cordova, KMM, Mac Catalyst, cualquier herramienta cross-platform.
- **Web NO se replica:** el portal Jinja sigue siendo el cliente principal de MANAGER/ADMIN para operación pesada. La app móvil consume `/api/v1/*` read-only y muestra subset relevante (login, mis convocatorias, mi posición, ranking admin, intento detalle).

## Por qué

Antonio quiere foco para el sprint del demo CMadrid del 11 de mayo:
- iPhone: alumno individual / instructor en campo.
- iPad: instructor / manager con vista más amplia.
- Watch: alerta cuando llegue un intento o cambio de estado relevante (notificación + glance).
- Mac y Vision son costo de mantenimiento sin valor para el cliente — el portal web ya cubre el desktop.
- Cross-platform mezcla idioms y rompe la promesa "se siente nativa". Si vamos a tener una app Apple, que sea Apple-first end to end.

## Dónde aplica

- `/Users/antoniohermoso/IOS/Dobacksoft Training/Dobacksoft Training.xcodeproj/project.pbxproj`:
  - `SUPPORTED_PLATFORMS = "iphoneos iphonesimulator"`. Sin `macosx`, sin `xros`, sin `xrsimulator`.
  - `TARGETED_DEVICE_FAMILY = "1,2"`. 1=iPhone, 2=iPad. Sin 7=Vision.
- En el código Swift: ningún `#if os(macOS)` ni `#if os(visionOS)` en lugares operativos. Si aparece (típicamente en plantillas de Xcode), eliminarlo.
- En decisiones de librerías: cualquier dep que tire `macOS` o `visionOS` como soporte adicional NO se usa salvo que también soporte iOS first-class y no implique código condicional.

## Cómo aplicarlo

- **Al revisar PRs del proyecto iOS:** rechazar cualquier cambio que agregue `macOS`, `visionOS`, `tvOS` a `SUPPORTED_PLATFORMS` o que incluya frameworks cross-platform en `Package.swift` / Cocoapods / SPM.
- **Al sugerir features:** preguntar siempre "¿esto es iPhone, iPad o Watch?". Si cae fuera, decir explícitamente "fuera de scope D-IOS-001".
- **Al adaptar para iPad:** usar `NavigationSplitView` cuando `horizontalSizeClass == .regular`; en iPhone usar `NavigationStack` + `TabView`. Una sola implementación SwiftUI con detección de size class.
- **Al construir el target Watch:** target separado, **comparte modelos Codable + APIClient lite** vía Swift Package interno o source files in shared group; NO comparte Views. Watch es resumen, no réplica.
- **Al actualizar Xcode:** si una versión nueva agrega Vision/Mac automáticamente al template, removerlos como primer commit del onboarding.

## Aprendido

- iOS 26 / Xcode 26.4 usa `PBXFileSystemSynchronizedRootGroup` — cualquier `.swift` en la carpeta del target se incluye sin tocar pbxproj. Eso ahorra fricción en la arquitectura modular Core/Features/Shared.
- El portal Jinja del repo `training` ya tiene login con cookies funcionando bien para web. La regla "no replicar web" significa que cualquier feature de UI compleja del portal (grids editables, formularios largos, exports legales) **se queda en web**. La app móvil es para "ver mi nota" y "tener notificación", no es ERP móvil.
- Watch sin iPhone parejado NO es soportado (por ahora). El usuario de Watch siempre tiene su iPhone con sesión activa.

## Cuándo se invalidaría

- Si CMadrid pide expresamente Mac/Vision Pro como requisito contractual (improbable; no figura en `docs/PROPUESTA-CMADRID.md`).
- Si Apple deprecara WatchKit y obligara a watchOS standalone, habría que reabrir la decisión del Watch.
- Si la operativa de campo necesitara un cliente desktop liviano (ej. instructor en aula con Mac) — pero ahí entra el portal web, no un binario nativo.

## Referencias

- engram: `architecture/ios-platform-rule` (id 928)
- engram: `architecture/mobile-api-strategy` (id 908) — la decisión madre de tener app móvil.
- contrato API que la app consume: [`docs/MOBILE-API.md`](../docs/MOBILE-API.md)
- proyecto Xcode: `/Users/antoniohermoso/IOS/Dobacksoft Training/`
