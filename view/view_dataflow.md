# View Layer: Datenfluesse und Kommunikationswege

Dieses Dokument beschreibt saemtliche Benutzerinteraktionen und die daraus resultierenden Datenfluesse durch alle drei Schichten der Anwendung. Es ergaenzt die bestehenden Dokumentationen (`view-doc.md`, `admin-mode-doc.md`, `core-doc.md`, `storage-doc.md`) um eine rein flussbasierte Top-Down-Sicht.

---

## Inhaltsverzeichnis

1. [Uebersicht aller Benutzerinteraktionen](#uebersicht-aller-benutzerinteraktionen)
2. [Anwendungsstart](#anwendungsstart)
3. [Visitor Mode: Layer-Auswahl (conv1 bis layer2)](#visitor-mode-layer-auswahl-conv1-bis-layer2)
4. [Visitor Mode: Layer-Auswahl (layer3, layer4)](#visitor-mode-layer-auswahl-layer3-layer4)
5. [Visitor Mode: Sprachwechsel](#visitor-mode-sprachwechsel)
6. [Visitor Mode: About oeffnen und schliessen](#visitor-mode-about-oeffnen-und-schliessen)
7. [Visitor Mode: Render-Loop](#visitor-mode-render-loop)
8. [Wechsel Visitor zu Admin Mode](#wechsel-visitor-zu-admin-mode)
9. [Wechsel Admin zu Visitor Mode](#wechsel-admin-zu-visitor-mode)
10. [Admin Mode: Layer-Auswahl](#admin-mode-layer-auswahl)
11. [Admin Mode: Preset-Auswahl](#admin-mode-preset-auswahl)
12. [Admin Mode: Parameter aendern (Live-Vorschau)](#admin-mode-parameter-aendern-live-vorschau)
13. [Admin Mode: Preset speichern](#admin-mode-preset-speichern)
14. [Admin Mode: Preset als aktiv markieren](#admin-mode-preset-als-aktiv-markieren)
15. [Admin Mode: Modus-Wechsel (Colormap/RGB)](#admin-mode-modus-wechsel-colormaprgb)
16. [Admin Mode: Channel hinzufuegen und entfernen](#admin-mode-channel-hinzufuegen-und-entfernen)
17. [Vollbild-Toggle](#vollbild-toggle)
18. [Anwendung schliessen](#anwendung-schliessen)

---

## Uebersicht aller Benutzerinteraktionen

| Interaktion | Ausloeser | Modus | Betroffene Layer |
|-------------|-----------|-------|------------------|
| Layer auswaehlen | Touch/Klick auf LayerButton | Visitor | View, Core |
| Sprache wechseln | Touch/Klick auf Language-Toggle | Visitor | View |
| About oeffnen/schliessen | Touch/Klick auf About-Icon | Visitor | View |
| Wechsel zu Admin Mode | Ctrl+A | Beide | View, Core |
| Wechsel zu Visitor Mode | ESC, Ctrl+V | Beide | View, Core |
| Layer auswaehlen | ComboBox-Aenderung | Admin | View, Core |
| Preset auswaehlen | ComboBox-Aenderung | Admin | View, Core |
| Parameter aendern | SpinBox, CheckBox, ComboBox | Admin | View, Core |
| Preset speichern | Klick auf Speichern-Button | Admin | View, Core, Storage |
| Preset als aktiv markieren | Klick auf Aktiv-Button | Admin | View, Core, Storage |
| Modus-Wechsel | RadioButton-Aenderung | Admin | View |
| Channel hinzufuegen/entfernen | Klick auf +/- Button | Admin | View, Core |
| Vollbild umschalten | F11 | Beide | View |
| Anwendung schliessen | Fenster schliessen | Beide | View, Core |

---

## Anwendungsstart

Der Benutzer startet die Anwendung ueber `python main.py`.

```
main.py
    |
    +--> Storage: ConfigManager instanziieren
    |        config_manager = ConfigManager("config.json")
    |
    +--> Core: Services instanziieren
    |        camera    = CameraService()
    |        model     = ModelService()
    |        vis       = VisualizationService()
    |        presets   = PresetService(config_manager)
    |
    +--> Core: Facade erstellen und initialisieren
    |        facade = ApplicationFacade(camera, model, vis, presets)
    |        facade.initialize()
    |            |
    |            +--> ModelService.load_model()
    |            |        ResNet18 in Speicher laden, Forward-Hooks registrieren
    |            |
    |            +--> CameraService.start()
    |            |        cv2.VideoCapture oeffnen
    |            |
    |            +--> PresetService: load_config()
    |            |        |
    |            |        +--> Storage: ConfigManager.load_config()
    |            |                 config.json lesen (oder Default erstellen)
    |            |
    |            +--> Facade._current_layer = "conv1" (erster Layer)
    |
    +--> View: MainWindow erstellen
             |
             +--> VisitorModeWidget(facade) erstellen
             |        _current_layer = "conv1"
             |        LayerButtonBar, InfoPanel, AboutWidget,
             |        OutputRankingWidget, GradCAMWidget erstellen
             |
             +--> AdminModeWidget(facade) erstellen
             |        _current_layer = "conv1"
             |        Layer-ComboBox, Preset-ComboBox,
             |        ChannelManager, PresetBuilder erstellen
             |
             +--> QStackedWidget: Index 0 (Visitor) aktiv
             |
             +--> MainWindow.switch_to_visitor_mode()
                      |
                      +--> VisitorModeWidget.start()
                               CameraThread erstellen und starten
```

---

## Visitor Mode: Layer-Auswahl (conv1 bis layer2)

Der Besucher tippt auf einen der Layer-Buttons. Fuer die Layer conv1, layer1 und layer2 ist kein GradCAM verfuegbar.

```
User tippt auf LayerButton
    |
    +--> LayerButtonBar.layer_selected Signal emittieren
             |
             +--> VisitorModeWidget._on_layer_selected(layer_name)
                      |
                      +--> _current_layer = layer_name
                      |
                      +--> Facade.change_layer(layer_name)
                      |        Facade._current_layer = layer_name
                      |
                      +--> _update_layer_info(layer_name)
                      |        LAYER_DESCRIPTIONS nachschlagen
                      |        InfoPanel.set_content(html)
                      |
                      +--> GradCAMWidget.set_current_layer(layer_name)
                      |        layer_name nicht in visible_layers
                      |        --> Widget wird unsichtbar
                      |
                      +--> CameraThread.change_layer(layer_name)
                               _target_layer = layer_name
                               (naechster Frame verwendet neuen Layer)
```

Ab diesem Zeitpunkt laeuft der Render-Loop (siehe Abschnitt "Visitor Mode: Render-Loop") mit dem neuen Layer weiter.

---

## Visitor Mode: Layer-Auswahl (layer3, layer4)

Der Besucher tippt auf einen der beiden letzten Layer. Zusaetzlich zum normalen Fluss wird das GradCAM-Widget sichtbar und empfaengt Daten.

```
User tippt auf LayerButton (layer3 oder layer4)
    |
    +--> LayerButtonBar.layer_selected Signal emittieren
             |
             +--> VisitorModeWidget._on_layer_selected(layer_name)
                      |
                      +--> _current_layer = layer_name
                      |
                      +--> Facade.change_layer(layer_name)
                      |        Facade._current_layer = layer_name
                      |
                      +--> _update_layer_info(layer_name)
                      |        InfoPanel.set_content(html)
                      |
                      +--> GradCAMWidget.set_current_layer(layer_name)
                      |        layer_name in visible_layers ["layer3", "layer4"]
                      |        --> Widget wird sichtbar
                      |
                      +--> GradCAMSubtitleWidget.set_current_layer(layer_name)
                      |        layer_name in visible_layers ["layer3", "layer4"]
                      |        --> Widget wird sichtbar
                      |
                      +--> CameraThread.change_layer(layer_name)
                               _target_layer = layer_name
```

Der Render-Loop erzeugt nun zusaetzlich GradCAM-Frames:

```
CameraThread Render-Loop (bei layer3/layer4)
    |
    +--> Facade.get_visualization_for_layer(layer_name)
    |        (normaler Visualisierungsfluss, siehe Render-Loop)
    |
    +--> frame_ready Signal --> CameraDisplayWidget.update_frame()
    |
    +--> predictions_ready Signal --> OutputRankingWidget.update_predictions()
    |        (throttled, alle 1s)
    |
    +--> Facade.compute_gradcam(layer_name)   [nur wenn layer in gradcam_layers]
    |        |                                 [throttled, alle 0.5s]
    |        +--> CameraService.get_frame()
    |        |        Kamera-Frame holen
    |        |
    |        +--> ModelService.compute_gradcam(frame, layer_name)
    |                 Forward+Backward Pass mit Gradienten
    |                 Heatmap-Overlay berechnen
    |                 --> RGB-Overlay-Bild (H, W, 3)
    |
    +--> gradcam_ready Signal --> GradCAMWidget.update_frame()
             Kreisfoermige Maskierung anwenden
             QLabel.setPixmap() aktualisieren
```

---

## Visitor Mode: Sprachwechsel

Der Besucher tippt auf das Flaggen-Icon. Dieser Fluss bleibt vollstaendig im View Layer.

```
User tippt auf Language-Toggle
    |
    +--> VisitorModeWidget._on_language_toggled()
             |
             +--> _language umschalten ("de" <-> "en")
             |
             +--> LayerButtonBar.update_language(language)
             |        Button-Texte aus BUTTON_LABELS aktualisieren
             |
             +--> AboutWidget.update_language(language)
             |        Seiteninhalte aus ABOUT_PAGES aktualisieren
             |
             +--> OutputRankingWidget.update_language(language)
             |        Titel und Klassennamen-Uebersetzung aktualisieren
             |
             +--> GradCAMWidget.update_language(language)
             |        Titel aktualisieren
             |
             +--> _update_layer_info(_current_layer)
             |        LAYER_DESCRIPTIONS[language] nachschlagen
             |        InfoPanel.set_content(html)
             |
             +--> language_changed Signal emittieren
                      |
                      +--> MainWindow._on_language_changed(language)
                               Window-Titel aus APP_TITLE aktualisieren
```

---

## Visitor Mode: About oeffnen und schliessen

Der Besucher tippt auf das Info-Icon. Das InfoPanel wird ausgeblendet, solange About geoeffnet ist.

```
User tippt auf About-Icon
    |
    +--> AboutWidget._expand()
             |
             +--> Content-Area sichtbar machen
             +--> Application-Level EventFilter installieren
             +--> expanded_changed Signal emittieren (True)
                      |
                      +--> VisitorModeWidget._on_about_expanded_changed(True)
                               InfoPanel.setVisible(False)

User tippt ausserhalb des AboutWidget (oder auf Schliessen)
    |
    +--> AboutWidget._collapse()
             |
             +--> Content-Area verstecken
             +--> Application-Level EventFilter entfernen
             +--> expanded_changed Signal emittieren (False)
                      |
                      +--> VisitorModeWidget._on_about_expanded_changed(False)
                               InfoPanel.setVisible(True)
```

---

## Visitor Mode: Render-Loop

Der CameraThread laeuft kontinuierlich und bildet die zentrale Rendering-Pipeline.

```
CameraThread.run() (Endlosschleife, ~30 FPS)
    |
    +--> Facade.get_visualization_for_layer(_target_layer)
    |        |
    |        +--> Core: CameraService.get_frame()
    |        |        cv2.VideoCapture.read()
    |        |        BGR --> RGB Konvertierung
    |        |        --> np.ndarray (H, W, 3)
    |        |
    |        +--> Core: ModelService.extract_layer_activations(frame, layer)
    |        |        Preprocessing (Resize 224x224, Normalize)
    |        |        Forward Pass (torch.no_grad)
    |        |        Hook speichert Aktivierungen
    |        |        Batch-Dimension entfernen
    |        |        --> torch.Tensor (C, H, W)
    |        |
    |        +--> Core: PresetService.get_active_preset(layer)
    |        |        In-Memory-Lookup
    |        |        --> PresetConfig
    |        |
    |        +--> Core: VisualizationService.visualize(activations, preset)
    |                 Channel-Auswahl (filtern von -1)
    |                 Blending (max/mean/overlay)
    |                 Normalisierung
    |                 Colormap oder RGB-Mapping
    |                 Resize auf 800x600
    |                 --> np.ndarray (600, 800, 3)
    |
    +--> frame_ready Signal emittieren
    |        |
    |        +--> CameraDisplayWidget.update_frame(frame)
    |                 numpy --> QImage --> QPixmap
    |                 QLabel.setPixmap() (skaliert)
    |
    +--> [throttled, alle 1s] predictions_ready Signal emittieren
    |        |
    |        +--> OutputRankingWidget.update_predictions(predictions)
    |                 ModelService.get_top_predictions() (gecachte Logits)
    |                 Top-3 Balkendiagramm aktualisieren
    |
    +--> [throttled, alle 0.5s, nur layer3/layer4] gradcam_ready Signal
             |
             +--> GradCAMWidget.update_frame(overlay)
                      Kreisfoermig maskieren, QLabel aktualisieren
```

---

## Wechsel Visitor zu Admin Mode

Der Benutzer drueckt Ctrl+A. Der Visitor-Layer wird ueber die Facade an den Admin Mode uebergeben.

```
User drueckt Ctrl+A
    |
    +--> MainWindow.switch_to_admin_mode()
             |
             +--> VisitorModeWidget.stop()
             |        |
             |        +--> Custom-Cursor entfernen, EventFilter deinstallieren
             |        +--> CameraThread.stop()
             |        |        _running = False, wait() (Thread-Join)
             |        +--> CameraThread = None
             |        +--> CameraDisplayWidget: clear(), setText("Kamera gestoppt")
             |
             +--> QStackedWidget.setCurrentIndex(1)  (Admin sichtbar)
             |
             +--> AdminModeWidget.start()
                      |
                      +--> Facade.get_current_layer()
                      |        --> z.B. "layer2" (vom Visitor geschrieben)
                      |
                      +--> Layer-ComboBox.setCurrentIndex(layer2_index)
                      |        |
                      |        +--> _on_layer_changed("layer2") [Signal]
                      |                 |
                      |                 +--> _current_layer = "layer2"
                      |                 |
                      |                 +--> Facade.get_layer_channel_count("layer2")
                      |                 |        --> 128
                      |                 |        ChannelManager.update_range(128)
                      |                 |
                      |                 +--> Facade.get_active_preset("layer2")
                      |                 |        --> PresetConfig (aktives Preset)
                      |                 |        Preset-ComboBox synchronisieren
                      |                 |
                      |                 +--> _load_current_preset()
                      |                          UI-Controls mit Preset-Werten befuellen
                      |
                      +--> Facade.get_active_preset(_current_layer)
                      |        Preset-Selector synchronisieren (falls noetig)
                      |
                      +--> CameraThread erstellen und starten
                      |        CameraThread(facade, _current_layer)
                      |        frame_ready --> _preview_display.update_frame
                      |        error_occurred --> _on_error_occurred
                      |
                      +--> _on_param_changed()
                               PresetBuilder.build_from_ui()
                               CameraThread.set_temp_preset(preset)
                               (Live-Vorschau zeigt sofort UI-Werte)
```

---

## Wechsel Admin zu Visitor Mode

Der Benutzer drueckt ESC oder Ctrl+V.

```
User drueckt ESC oder Ctrl+V
    |
    +--> MainWindow.switch_to_visitor_mode()
             |
             +--> AdminModeWidget.stop()
             |        |
             |        +--> CameraThread.stop()
             |        |        _running = False, wait() (Thread-Join)
             |        +--> CameraThread = None
             |        +--> CameraDisplayWidget: clear(), setText("Vorschau gestoppt")
             |
             +--> QStackedWidget.setCurrentIndex(0)  (Visitor sichtbar)
             |
             +--> VisitorModeWidget.start()
                      |
                      +--> Custom-Cursor setzen, EventFilter installieren
                      |
                      +--> CameraThread erstellen und starten
                               CameraThread(facade, _current_layer)
                               frame_ready --> _camera_display.update_frame
                               predictions_ready --> _output_ranking.update_predictions
                               gradcam_ready --> _gradcam_widget.update_frame
                               GradCAM-Layers setzen (layer3, layer4)
                               Thread starten
```

Der Visitor-Mode startet mit seinem eigenen `_current_layer`, der sich unabhaengig vom Admin-Mode-State erhalten hat.

---

## Admin Mode: Layer-Auswahl

Der Benutzer waehlt einen Layer in der ComboBox.

```
User aendert Layer-ComboBox
    |
    +--> AdminModeWidget._on_layer_changed(layer_name)
             |
             +--> _current_layer = layer_name
             |
             +--> Core: Facade.get_layer_channel_count(layer_name)
             |        --> ModelService: Hardcoded Channel-Count nachschlagen
             |        --> int (z.B. 128 fuer layer2)
             |
             +--> ChannelManager.update_range(channel_count)
             |        SpinBox-Maxima anpassen (Colormap und RGB)
             |        Werte klemmen falls ausserhalb des neuen Bereichs
             |
             +--> Core: Facade.get_active_preset(layer_name)
             |        --> PresetService: In-Memory-Lookup
             |        --> PresetConfig (aktives Preset des neuen Layers)
             |
             +--> Preset-ComboBox.setCurrentIndex(active_preset_id)
             |
             +--> _load_current_preset()
             |        Facade.get_preset(layer_name, preset_id)
             |        UI-Controls mit Preset-Werten befuellen
             |        (RadioButtons, SpinBoxes, ComboBoxes, CheckBoxes)
             |
             +--> [nur wenn CameraThread laeuft]
                      CameraThread.change_layer(layer_name)
                      _on_param_changed()
                           PresetBuilder.build_from_ui()
                           CameraThread.set_temp_preset(preset)
```

---

## Admin Mode: Preset-Auswahl

Der Benutzer waehlt ein Preset in der ComboBox.

```
User aendert Preset-ComboBox
    |
    +--> AdminModeWidget._on_preset_changed(preset_index)
             |
             +--> _current_preset_id = preset_index
             |
             +--> _load_current_preset()
             |        |
             |        +--> Core: Facade.get_preset(_current_layer, preset_index)
             |        |        --> PresetService: In-Memory-Lookup
             |        |        --> PresetConfig
             |        |
             |        +--> UI aktualisieren:
             |                 Preset-Name Label setzen
             |                 RadioButtons (Colormap/RGB) setzen
             |                 ChannelManager: Channels laden
             |                 Colormap-ComboBox setzen
             |                 Normalize-CheckBox setzen
             |                 Blend-Mode-ComboBox setzen
             |
             +--> _on_param_changed()
                      PresetBuilder.build_from_ui()
                      CameraThread.set_temp_preset(preset)
                      (Live-Vorschau zeigt sofort das neue Preset)
```

---

## Admin Mode: Parameter aendern (Live-Vorschau)

Der Benutzer aendert einen beliebigen Parameter (Channel-SpinBox, Colormap, Normalize, Blend-Mode).

```
User aendert beliebigen Parameter
    |
    +--> AdminModeWidget._on_param_changed()
             |
             +--> PresetBuilder.build_from_ui(
             |        preset_id, name,
             |        is_rgb_mode, channels, rgb_channels,
             |        colormap, normalize, blend_mode
             |    )
             |    --> PresetConfig (temporaer, nicht gespeichert)
             |
             +--> CameraThread.set_temp_preset(preset)
                      _temp_preset = preset
                      |
                      (naechster Frame im Render-Loop:)
                      +--> Facade.get_visualization_with_preset(layer, preset)
                               |
                               +--> CameraService.get_frame()
                               +--> ModelService.extract_layer_activations()
                               +--> VisualizationService.visualize(activations, temp_preset)
                               |        (verwendet temporaeres Preset statt aktivem)
                               +--> frame_ready --> CameraDisplayWidget.update_frame()
```

---

## Admin Mode: Preset speichern

Der Benutzer klickt auf "Preset speichern".

```
User klickt auf "Preset speichern"
    |
    +--> AdminModeWidget._save_current_preset()
             |
             +--> Core: Facade.get_preset(_current_layer, _current_preset_id)
             |        --> PresetConfig (fuer den Preset-Namen)
             |
             +--> PresetBuilder.build_from_ui(...)
             |        --> PresetConfig (mit aktuellem Preset-Namen)
             |
             +--> Core: Facade.save_preset(layer, preset_id, preset)
             |        |
             |        +--> PresetService.save_preset(layer, preset_id, preset)
             |                 |
             |                 +--> In-Memory-Config aktualisieren
             |                 |        LayerPresets.presets[preset_id] = preset
             |                 |
             |                 +--> Storage: ConfigManager.save_config(config)
             |                          |
             |                          +--> Serialisierung: Python --> dict --> JSON
             |                          +--> Atomarer Schreibvorgang:
             |                                   config.tmp schreiben
             |                                   config.tmp --> config.json (replace)
             |
             +--> QMessageBox.information("Erfolg")
```

---

## Admin Mode: Preset als aktiv markieren

Der Benutzer klickt auf "Als aktiv markieren".

```
User klickt auf "Als aktiv markieren"
    |
    +--> AdminModeWidget._set_as_active_preset()
             |
             +--> Core: Facade.set_active_preset(layer, preset_id)
             |        |
             |        +--> PresetService.set_active_preset(layer, preset_id)
             |                 |
             |                 +--> In-Memory: LayerPresets.active_preset_id = preset_id
             |                 |
             |                 +--> Storage: ConfigManager.save_config(config)
             |                          Atomarer Schreibvorgang (wie oben)
             |
             +--> QMessageBox.information("Erfolg")
```

Dieses Preset wird ab sofort im Visitor Mode fuer den betreffenden Layer verwendet, da der Render-Loop `get_active_preset()` aufruft.

---

## Admin Mode: Modus-Wechsel (Colormap/RGB)

Der Benutzer wechselt zwischen Colormap und RGB Modus.

```
User klickt auf RadioButton (Colormap oder RGB)
    |
    +--> AdminModeWidget._on_mode_changed(checked)
             |
             +--> UI-Gruppen umschalten:
             |        Colormap-GroupBox sichtbar/unsichtbar
             |        RGB-GroupBox sichtbar/unsichtbar
             |        Normalize-CheckBox sichtbar/unsichtbar
             |        Blend-Mode-Row sichtbar/unsichtbar
             |
             +--> [bei Wechsel zu RGB]
             |        Normalize auf True erzwingen
             |        Blend-Mode auf "max" erzwingen
             |
             +--> _on_param_changed()
                      (Live-Vorschau aktualisieren, siehe oben)
```

---

## Admin Mode: Channel hinzufuegen und entfernen

Der Benutzer klickt auf "+" oder "-" Buttons bei den Colormap-Channels.

```
User klickt auf "+" (Channel hinzufuegen)
    |
    +--> AdminModeWidget._on_add_channel()
             |
             +--> ChannelManager.add_channel()
             |        Naechsten inaktiven Channel-Row sichtbar machen
             |        SpinBox-Wert auf 0 setzen (programmatisch)
             |        Delete-Button sichtbar machen
             |        Add-Button verstecken falls 3 Channels aktiv
             |
             +--> _on_param_changed()
                      (Live-Vorschau aktualisieren)

User klickt auf "-" (Channel entfernen)
    |
    +--> AdminModeWidget._on_delete_channel(index)
             |
             +--> ChannelManager.delete_channel(index)
             |        Channel-Row verstecken
             |        Nachfolgende Channels aufruecken lassen
             |        SpinBox-Wert auf -1 setzen (Sentinel)
             |        Add-Button wieder sichtbar machen
             |
             +--> _on_param_changed()
                      (Live-Vorschau aktualisieren)
```

---

## Vollbild-Toggle

Der Benutzer drueckt F11. Dieser Fluss bleibt vollstaendig im View Layer.

```
User drueckt F11
    |
    +--> MainWindow.toggle_fullscreen()
             |
             +--> [wenn Vollbild aktiv]
             |        showNormal()
             |        resizeEvent --> VisitorModeWidget._position_overlays()
             |
             +--> [wenn Fenster-Modus aktiv]
                      showFullScreen()
                      resizeEvent --> VisitorModeWidget._position_overlays()
                           Alle Overlays neu positionieren:
                           Frame-Overlay, ButtonBar, InfoPanel,
                           Icon-Bar, AboutWidget, Language-Toggle,
                           OutputRanking, GradCAMWidget
```

---

## Anwendung schliessen

Der Benutzer schliesst das Fenster.

```
User schliesst Fenster
    |
    +--> MainWindow.closeEvent()
             |
             +--> VisitorModeWidget.stop()
             |        CameraThread.stop() (falls laufend)
             |        Custom-Cursor entfernen
             |
             +--> AdminModeWidget.stop()
             |        CameraThread.stop() (falls laufend)
             |
             +--> event.accept()
             |
             +--> (main.py) Facade.shutdown()
                      |
                      +--> Core: CameraService.stop()
                               cv2.VideoCapture freigeben
```
