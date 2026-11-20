// BroccoliVoice — the dictation helper of Broccoli (2026-11-16).
// Apple's on-device speech recognizer (SpeechAnalyzer, macOS 26+) can only be reached from
// Swift, so this small program does the listening and the recognizing and reports to Broccoli
// as one JSON object per line on stdout:
//   {"type":"check", ...}                      answer to --check
//   {"type":"asset","state":"downloading","progress":0.4} / {"type":"asset","state":"ready"}
//   {"type":"ready"}                           the microphone is open
//   {"type":"level","value":0.0–1.0,"tone":0.0–1.0}   loudness, about 15 a second; tone = how high the
//                                              voice is (from how often the sound wave crosses zero)
//   {"type":"partial","text":"…"}              text that may still change
//   {"type":"final","text":"…"}                text that will not change any more
//   {"type":"error","code":"…","detail":"…"}   codes only: Broccoli translates them
//   {"type":"done"}
// It stops when it reads the line "stop" on stdin, or when stdin closes.
// --save <file.caf>: what the microphone hears is also written to that file as it comes (a long
// recording that is kept, Broccoli's "recording"); {"type":"saving","path":"…"} says it is.
//
// For the speech models Broccoli runs itself (Settings › Models › Local models):
//   BroccoliVoice --capture [--device <id>] [--file <path>]
// only listens: stdout carries the sound itself — 16 kHz, one channel, 16-bit little-endian
// samples, nothing else — and stderr the JSON lines ({"type":"ready"}, errors, {"type":"done"}).
// "stop" on stdin ends it. --file sends a sound file instead of the microphone (tests; with
// --pace at the speed it was spoken).
//
// It also answers for the Mac's own language model (Apple Intelligence, FoundationModels):
//   BroccoliVoice --chat      reads ONE JSON object on stdin:
//       {"messages":[{"role":"system"|"user"|"assistant","content":"…"}], "temperature":0.7, "max_tokens":800}
//   and reports {"type":"delta","text":"…"} as the answer grows, then {"type":"done"};
//   errors: model_unavailable (detail: not_enabled | not_eligible | not_ready), context_too_long,
//   refused, chat_failed.
//
// --system (with the listening or with --capture; 2026-11-19): the sound comes from what this Mac
// is playing — every program's sound, the other side of an online meeting — instead of the
// microphone (a Core Audio tap, macOS 14.2+; nothing is installed, what is heard is not changed).
// Errors: system_audio_denied (the user said no to recording the Mac's sound),
// system_audio_unavailable.
//   BroccoliVoice --output    says where this Mac's sound comes out right now:
//       {"type":"output","kind":"speaker"|"headphones"|"unknown","name":"…"}
// Build: voice_input/build.sh      Plan: editor_handoff/PLAN_20261116_语音输入与本地模型.md
import Foundation
import Speech
import AVFoundation
import CoreAudio
import AudioToolbox
import FoundationModels

let outLock = NSLock()

func emit(_ object: [String: Any]) {
    guard let data = try? JSONSerialization.data(withJSONObject: object, options: []) else { return }
    outLock.lock()
    defer { outLock.unlock() }
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([0x0A]))
}

func fail(_ code: String, _ detail: String = "") {
    emit(["type": "error", "code": code, "detail": detail])
}

func argument(_ name: String) -> String? {
    let args = CommandLine.arguments
    guard let index = args.firstIndex(of: name), index + 1 < args.count else { return nil }
    return args[index + 1]
}

func microphoneState() -> String {
    switch AVCaptureDevice.authorizationStatus(for: .audio) {
    case .authorized: return "allowed"
    case .denied: return "denied"
    case .restricted: return "restricted"
    default: return "not_asked"
    }
}

func inputDevices() -> [[String: String]] {
    let session = AVCaptureDevice.DiscoverySession(
        deviceTypes: [.microphone, .external], mediaType: .audio, position: .unspecified)
    return session.devices.map { ["id": $0.uniqueID, "name": $0.localizedName] }
}

func audioDeviceID(forUID uid: String) -> AudioDeviceID? {
    var address = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyTranslateUIDToDevice,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain)
    var cfUID = uid as CFString
    var device = AudioDeviceID(kAudioObjectUnknown)
    var size = UInt32(MemoryLayout<AudioDeviceID>.size)
    let status = withUnsafeMutablePointer(to: &cfUID) { pointer in
        AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address,
                                   UInt32(MemoryLayout<CFString>.size), pointer, &size, &device)
    }
    return (status == noErr && device != kAudioObjectUnknown) ? device : nil
}

func languageModelState() -> String {
    switch SystemLanguageModel.default.availability {
    case .available:
        return "available"
    case .unavailable(let reason):
        switch reason {
        case .appleIntelligenceNotEnabled: return "not_enabled"
        case .deviceNotEligible: return "not_eligible"
        case .modelNotReady: return "not_ready"
        @unknown default: return "unavailable"
        }
    }
}

func runChat() async {
    let input = FileHandle.standardInput.readDataToEndOfFile()
    guard let request = (try? JSONSerialization.jsonObject(with: input)) as? [String: Any],
          let messages = request["messages"] as? [[String: Any]], !messages.isEmpty else {
        fail("chat_failed", "bad request")
        return
    }
    let state = languageModelState()
    guard state == "available" else { fail("model_unavailable", state); return }
    func text(_ message: [String: Any]) -> String {
        if let content = message["content"] as? String { return content }
        if let parts = message["content"] as? [[String: Any]] {      // [{"type":"text","text":"…"}, …]
            return parts.compactMap { $0["text"] as? String }.joined(separator: "\n")
        }
        return ""
    }
    var instructions: [String] = []
    var turns: [(role: String, text: String)] = []
    for message in messages {
        let role = (message["role"] as? String) ?? "user"
        let content = text(message)
        if content.isEmpty { continue }
        if role == "system" || role == "developer" { instructions.append(content) } else { turns.append((role, content)) }
    }
    guard let last = turns.last else { fail("chat_failed", "no question"); return }
    // earlier turns go in as the conversation so far
    var entries: [Transcript.Entry] = []
    if !instructions.isEmpty {
        entries.append(.instructions(Transcript.Instructions(
            segments: [.text(Transcript.TextSegment(content: instructions.joined(separator: "\n\n")))], toolDefinitions: [])))
    }
    for turn in turns.dropLast() {
        let segment = Transcript.Segment.text(Transcript.TextSegment(content: turn.text))
        if turn.role == "assistant" {
            entries.append(.response(Transcript.Response(assetIDs: [], segments: [segment])))
        } else {
            entries.append(.prompt(Transcript.Prompt(segments: [segment])))
        }
    }
    let session = LanguageModelSession(model: SystemLanguageModel.default, transcript: Transcript(entries: entries))
    var options = GenerationOptions()
    if let temperature = request["temperature"] as? Double { options.temperature = temperature }
    if let limit = (request["max_tokens"] as? Int) ?? (request["max_completion_tokens"] as? Int), limit > 0 {
        options.maximumResponseTokens = limit
    }
    do {
        var sent = ""
        for try await snapshot in session.streamResponse(to: last.text, options: options) {
            let whole = snapshot.content
            if whole.count > sent.count, whole.hasPrefix(sent) {
                emit(["type": "delta", "text": String(whole.dropFirst(sent.count))])
                sent = whole
            } else if whole != sent {
                emit(["type": "replace", "text": whole])
                sent = whole
            }
        }
    } catch let error as LanguageModelSession.GenerationError {
        switch error {
        case .exceededContextWindowSize: fail("context_too_long", "\(error)")
        case .guardrailViolation, .refusal: fail("refused", "\(error)")
        default: fail("chat_failed", "\(error)")
        }
    } catch {
        // other error types say what happened only in words
        let words = "\(error)".lowercased()
        if words.contains("context") { fail("context_too_long", "\(error)") }
        else if words.contains("unsafe") || words.contains("guardrail") { fail("refused", "\(error)") }
        else { fail("chat_failed", "\(error)") }
    }
}

func runCheck() async {
    let supported = await SpeechTranscriber.supportedLocales.map { $0.identifier(.bcp47) }.sorted()
    let installed = await SpeechTranscriber.installedLocales.map { $0.identifier(.bcp47) }.sorted()
    emit([
        "type": "check",
        "available": SpeechTranscriber.isAvailable,
        "supported_locales": supported,
        "installed_locales": installed,
        "microphone": microphoneState(),
        "devices": inputDevices(),
        "default_device": AVCaptureDevice.default(for: .audio)?.uniqueID ?? "",
        "language_model": languageModelState(),
    ])
}

func waitForStop() async {
    await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in
        Thread.detachNewThread {
            while let line = readLine() {
                if line.trimmingCharacters(in: .whitespacesAndNewlines) == "stop" { break }
            }
            continuation.resume()
        }
    }
}

final class LevelMeter {
    private var last = Date.distantPast
    func report(_ buffer: AVAudioPCMBuffer) {
        let now = Date()
        guard now.timeIntervalSince(last) >= 0.066, let channel = buffer.floatChannelData?[0] else { return }
        last = now
        let count = Int(buffer.frameLength)
        guard count > 0 else { return }
        // (the Mac's own sound comes with its channels interleaved: the first one is every stride-th sample)
        let stride = buffer.format.isInterleaved ? max(1, Int(buffer.format.channelCount)) : 1
        var sum: Float = 0
        var crossings = 0
        for index in 0..<count {
            let value = channel[index * stride]
            sum += value * value
            if index > 0, (value >= 0) != (channel[(index - 1) * stride] >= 0) { crossings += 1 }
        }
        let rms = (sum / Float(count)).squareRoot()
        // -50 dB … 0 dB → 0 … 1
        let level = max(0, min(1, (20 * log10(max(rms, 1e-6)) + 50) / 50))
        // about the pitch: crossings a second / 2; 90 Hz … 2000 Hz → 0 … 1 (evenly by octave)
        let hertz = Double(crossings) * buffer.format.sampleRate / (2.0 * Double(count))
        let tone = max(0, min(1, log2(max(hertz, 90.0) / 90.0) / log2(2000.0 / 90.0)))
        emit(["type": "level", "value": Double((level * 100).rounded() / 100), "tone": (tone * 100).rounded() / 100])
    }
}

// ── the Mac's own sound (--system) ───────────────────────────────────────────────────────────
// Whether Broccoli may record what the Mac plays is kept by the system under "System Audio
// Recording"; there is no public call that only asks "may I?", so the system's own lookup is
// used when it is there (without it: "unknown", and the recording is simply tried).
private typealias SoundPermissionLookup = @convention(c) (CFString, CFDictionary?) -> Int
private typealias SoundPermissionRequest = @convention(c) (CFString, CFDictionary?, @escaping @convention(block) (Bool) -> Void) -> Void
private func soundPermissionSymbol(_ name: String) -> UnsafeMutableRawPointer? {
    guard let library = dlopen("/System/Library/PrivateFrameworks/TCC.framework/Versions/A/TCC", RTLD_NOW) else { return nil }
    return dlsym(library, name)
}

func systemSoundState() -> String {
    guard let symbol = soundPermissionSymbol("TCCAccessPreflight") else { return "unknown" }
    switch unsafeBitCast(symbol, to: SoundPermissionLookup.self)("kTCCServiceAudioCapture" as CFString, nil) {
    case 0: return "allowed"
    case 1: return "denied"
    default: return "not_asked"
    }
}

func askForSystemSound() async -> Bool {
    guard let symbol = soundPermissionSymbol("TCCAccessRequest") else { return true }
    let request = unsafeBitCast(symbol, to: SoundPermissionRequest.self)
    return await withCheckedContinuation { (continuation: CheckedContinuation<Bool, Never>) in
        request("kTCCServiceAudioCapture" as CFString, nil) { allowed in continuation.resume(returning: allowed) }
    }
}

final class SystemSound {
    let format: AVAudioFormat
    private var tapID = AudioObjectID(kAudioObjectUnknown)
    private var deviceID = AudioObjectID(kAudioObjectUnknown)
    private var procID: AudioDeviceIOProcID?
    private let queue = DispatchQueue(label: "broccoli.system-sound")

    /// nil = it could not be set up; `problem` says at which step
    init?(problem: inout String) {
        // 1. the tap: everything every program plays, mixed down to two channels; nobody hears a difference
        let description = CATapDescription(stereoGlobalTapButExcludeProcesses: [])
        description.uuid = UUID()
        description.isPrivate = true
        description.muteBehavior = .unmuted
        description.name = "Broccoli"
        var tap = AudioObjectID(kAudioObjectUnknown)
        var status = AudioHardwareCreateProcessTap(description, &tap)
        guard status == noErr else { problem = "tap \(status)"; return nil }
        var address = AudioObjectPropertyAddress(mSelector: kAudioTapPropertyFormat,
                                                 mScope: kAudioObjectPropertyScopeGlobal,
                                                 mElement: kAudioObjectPropertyElementMain)
        var stream = AudioStreamBasicDescription()
        var size = UInt32(MemoryLayout<AudioStreamBasicDescription>.size)
        status = AudioObjectGetPropertyData(tap, &address, 0, nil, &size, &stream)
        guard status == noErr, let tapFormat = AVAudioFormat(streamDescription: &stream) else {
            AudioHardwareDestroyProcessTap(tap)
            problem = "format \(status)"; return nil
        }
        // 2. a device of our own that carries only the tap, so it can be read like a microphone
        //    (private: no other program sees it; it does not depend on which speakers are in use)
        let device: [String: Any] = [
            kAudioAggregateDeviceNameKey: "Broccoli",
            kAudioAggregateDeviceUIDKey: UUID().uuidString,
            kAudioAggregateDeviceIsPrivateKey: true,
            kAudioAggregateDeviceIsStackedKey: false,
            kAudioAggregateDeviceTapAutoStartKey: true,
            kAudioAggregateDeviceTapListKey: [[kAudioSubTapUIDKey: description.uuid.uuidString,
                                               kAudioSubTapDriftCompensationKey: true]],
        ]
        var made = AudioObjectID(kAudioObjectUnknown)
        status = AudioHardwareCreateAggregateDevice(device as CFDictionary, &made)
        guard status == noErr else {
            AudioHardwareDestroyProcessTap(tap)
            problem = "device \(status)"; return nil
        }
        format = tapFormat
        tapID = tap
        deviceID = made
    }

    /// `handler` gets each piece of sound as it is played (the buffer is only good during the call)
    func start(_ handler: @escaping (AVAudioPCMBuffer) -> Void) -> Bool {
        let format = self.format
        var status = AudioDeviceCreateIOProcIDWithBlock(&procID, deviceID, queue) { _, input, _, _, _ in
            guard let buffer = AVAudioPCMBuffer(pcmFormat: format, bufferListNoCopy: input, deallocator: nil),
                  buffer.frameLength > 0 else { return }
            handler(buffer)
        }
        guard status == noErr, let procID else { return false }
        status = AudioDeviceStart(deviceID, procID)
        return status == noErr
    }

    func stop() {
        if let procID {
            AudioDeviceStop(deviceID, procID)
            AudioDeviceDestroyIOProcID(deviceID, procID)
        }
        procID = nil
        queue.sync {}                   // the piece being handled right now is finished
        if deviceID != kAudioObjectUnknown { AudioHardwareDestroyAggregateDevice(deviceID) }
        if tapID != kAudioObjectUnknown { AudioHardwareDestroyProcessTap(tapID) }
        deviceID = AudioObjectID(kAudioObjectUnknown)
        tapID = AudioObjectID(kAudioObjectUnknown)
    }
}

/// The Mac's sound, ready to start — or nil after `report(code, detail)` said why not.
func openSystemSound(_ report: (String, String) -> Void) async -> SystemSound? {
    var state = systemSoundState()
    if state == "not_asked" {           // the system asks the user now (once)
        state = await askForSystemSound() ? "allowed" : "denied"
    }
    guard state != "denied" else { report("system_audio_denied", ""); return nil }
    var problem = ""
    guard let sound = SystemSound(problem: &problem) else { report("system_audio_unavailable", problem); return nil }
    return sound
}

/// Where this Mac's sound comes out right now (--output).
func runOutput() {
    var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultOutputDevice,
                                             mScope: kAudioObjectPropertyScopeGlobal,
                                             mElement: kAudioObjectPropertyElementMain)
    var device = AudioDeviceID(kAudioObjectUnknown)
    var size = UInt32(MemoryLayout<AudioDeviceID>.size)
    guard AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &size, &device) == noErr,
          device != kAudioObjectUnknown else {
        emit(["type": "output", "kind": "unknown", "name": ""]); return
    }
    func number(_ selector: AudioObjectPropertySelector, _ scope: AudioObjectPropertyScope) -> UInt32? {
        var address = AudioObjectPropertyAddress(mSelector: selector, mScope: scope, mElement: kAudioObjectPropertyElementMain)
        var value: UInt32 = 0
        var size = UInt32(MemoryLayout<UInt32>.size)
        return AudioObjectGetPropertyData(device, &address, 0, nil, &size, &value) == noErr ? value : nil
    }
    var name = "" as CFString
    address = AudioObjectPropertyAddress(mSelector: kAudioObjectPropertyName, mScope: kAudioObjectPropertyScopeGlobal,
                                         mElement: kAudioObjectPropertyElementMain)
    size = UInt32(MemoryLayout<CFString>.size)
    _ = withUnsafeMutablePointer(to: &name) { AudioObjectGetPropertyData(device, &address, 0, nil, &size, $0) }
    let words = (name as String).lowercased()
    let transport = number(kAudioDevicePropertyTransportType, kAudioObjectPropertyScopeGlobal) ?? 0
    let source = number(kAudioDevicePropertyDataSource, kAudioDevicePropertyScopeOutput) ?? 0
    let headphoneSource: UInt32 = 0x6864706E          // 'hdpn'
    var kind = "unknown"
    if ["headphone", "headset", "earphone", "airpods", "buds"].contains(where: { words.contains($0) }) {
        kind = "headphones"
    } else if ["speaker", "display"].contains(where: { words.contains($0) }) {
        kind = "speaker"
    } else {
        switch transport {
        case kAudioDeviceTransportTypeBuiltIn:
            kind = source == headphoneSource ? "headphones" : "speaker"
        case kAudioDeviceTransportTypeBluetooth, kAudioDeviceTransportTypeBluetoothLE:
            kind = "headphones"         // (a Bluetooth loudspeaker cannot be told apart: taken as worn)
        case kAudioDeviceTransportTypeHDMI, kAudioDeviceTransportTypeDisplayPort, kAudioDeviceTransportTypeAirPlay:
            kind = "speaker"
        default:
            kind = "unknown"
        }
    }
    emit(["type": "output", "kind": kind, "name": name as String])
}

func runListen(localeID: String, deviceUID: String?, filePath: String?) async {
    guard SpeechTranscriber.isAvailable else { fail("speech_unavailable"); return }
    guard let locale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale(identifier: localeID)) else {
        fail("language_unsupported", localeID)
        return
    }
    let transcriber = SpeechTranscriber(locale: locale, transcriptionOptions: [],
                                        reportingOptions: [.volatileResults], attributeOptions: [])
    // the language's model: the system downloads it once and keeps it
    do {
        if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            emit(["type": "asset", "state": "downloading", "progress": 0.0])
            let watcher = Task {
                while !Task.isCancelled {
                    try? await Task.sleep(nanoseconds: 500_000_000)
                    if Task.isCancelled { break }
                    emit(["type": "asset", "state": "downloading",
                          "progress": (request.progress.fractionCompleted * 100).rounded() / 100])
                }
            }
            defer { watcher.cancel() }
            try await request.downloadAndInstall()
            emit(["type": "asset", "state": "ready"])
        }
    } catch {
        fail("language_download_failed", "\(error)")
        return
    }

    let analyzer = SpeechAnalyzer(modules: [transcriber])
    let results = Task {
        do {
            for try await result in transcriber.results {
                emit(["type": result.isFinal ? "final" : "partial", "text": String(result.text.characters)])
            }
        } catch {
            fail("recognition_failed", "\(error)")
        }
    }

    do {
        if let filePath {
            let file = try AVAudioFile(forReading: URL(fileURLWithPath: filePath))
            emit(["type": "ready"])
            if let last = try await analyzer.analyzeSequence(from: file) {
                try await analyzer.finalizeAndFinish(through: last)
            } else {
                await analyzer.cancelAndFinishNow()
            }
        } else {
            let fromSystem = CommandLine.arguments.contains("--system")
            if !fromSystem {
                if AVCaptureDevice.authorizationStatus(for: .audio) == .notDetermined {
                    _ = await AVCaptureDevice.requestAccess(for: .audio)
                }
                guard AVCaptureDevice.authorizationStatus(for: .audio) == .authorized else {
                    results.cancel()
                    fail("microphone_" + microphoneState())
                    return
                }
            }
            guard let format = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber]) else {
                results.cancel()
                fail("audio_format_unavailable")
                return
            }
            let engine = AVAudioEngine()
            var sound: SystemSound? = nil
            let inputFormat: AVAudioFormat
            if fromSystem {
                guard let opened = await openSystemSound({ fail($0, $1) }) else {
                    results.cancel()
                    return
                }
                sound = opened
                inputFormat = opened.format
            } else {
                let input = engine.inputNode
                if let deviceUID, !deviceUID.isEmpty {
                    // the microphone picked in Settings; not connected right now = the system's one
                    if var device = audioDeviceID(forUID: deviceUID), let unit = input.audioUnit,
                       AudioUnitSetProperty(unit, kAudioOutputUnitProperty_CurrentDevice, kAudioUnitScope_Global, 0,
                                            &device, UInt32(MemoryLayout<AudioDeviceID>.size)) == noErr {
                        emit(["type": "device", "id": deviceUID])
                    } else {
                        emit(["type": "device", "id": "", "missing": deviceUID])
                    }
                }
                inputFormat = input.outputFormat(forBus: 0)
            }
            guard inputFormat.sampleRate > 0, let converter = AVAudioConverter(from: inputFormat, to: format) else {
                results.cancel()
                fail("input_device_unusable")
                return
            }
            let (stream, feeder) = AsyncStream<AnalyzerInput>.makeStream()
            let meter = LevelMeter()
            // the recording kept on disk: the same sound the recognizer gets, written as it comes
            // (a .caf file can be read back even when it was never closed properly)
            var keep: AVAudioFile? = nil
            if let savePath = argument("--save"), !savePath.isEmpty {
                keep = try? AVAudioFile(forWriting: URL(fileURLWithPath: savePath), settings: format.settings,
                                        commonFormat: format.commonFormat, interleaved: format.isInterleaved)
                if keep != nil { emit(["type": "saving", "path": savePath]) }
                else { fail("recording_not_saved", savePath) }
            }
            let keeping = keep
            let ratio = format.sampleRate / inputFormat.sampleRate
            let heard: (AVAudioPCMBuffer) -> Void = { buffer in
                meter.report(buffer)
                let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 32
                guard let converted = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: capacity) else { return }
                var fed = false
                var problem: NSError?
                converter.convert(to: converted, error: &problem) { _, status in
                    if fed {
                        status.pointee = .noDataNow
                        return nil
                    }
                    fed = true
                    status.pointee = .haveData
                    return buffer
                }
                if problem == nil, converted.frameLength > 0 {
                    try? keeping?.write(from: converted)
                    feeder.yield(AnalyzerInput(buffer: converted))
                }
            }
            if let sound {
                guard sound.start(heard) else {
                    sound.stop()
                    results.cancel()
                    fail("system_audio_unavailable", "start")
                    return
                }
            } else {
                engine.inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { buffer, _ in heard(buffer) }
                engine.prepare()
                try engine.start()
            }
            try await analyzer.start(inputSequence: stream)
            emit(["type": "ready"])
            await waitForStop()
            if let sound {
                sound.stop()
            } else {
                engine.inputNode.removeTap(onBus: 0)
                engine.stop()
            }
            feeder.finish()
            try await analyzer.finalizeAndFinishThroughEndOfInput()
        }
    } catch {
        fail("recognition_failed", "\(error)")
        // nothing more will come: end the results stream, or the wait below never returns
        await analyzer.cancelAndFinishNow()
        results.cancel()
    }
    await results.value
}

func note(_ object: [String: Any]) {      // --capture: the JSON lines go to stderr, stdout is sound
    guard let data = try? JSONSerialization.data(withJSONObject: object, options: []) else { return }
    FileHandle.standardError.write(data)
    FileHandle.standardError.write(Data([0x0A]))
}

func runCapture(deviceUID: String?, filePath: String?) async {
    guard let wanted = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: 16000, channels: 1, interleaved: true) else {
        note(["type": "error", "code": "audio_format_unavailable"]); return
    }
    let out = FileHandle.standardOutput
    func write(_ buffer: AVAudioPCMBuffer) {
        guard buffer.frameLength > 0, let samples = buffer.int16ChannelData?[0] else { return }
        out.write(Data(bytes: samples, count: Int(buffer.frameLength) * 2))
    }
    func convert(_ converter: AVAudioConverter, _ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer? {
        let ratio = 16000.0 / buffer.format.sampleRate
        guard let converted = AVAudioPCMBuffer(pcmFormat: wanted, frameCapacity: AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 64) else { return nil }
        var fed = false
        var problem: NSError?
        converter.convert(to: converted, error: &problem) { _, status in
            if fed { status.pointee = .noDataNow; return nil }
            fed = true
            status.pointee = .haveData
            return buffer
        }
        return problem == nil ? converted : nil
    }
    if let filePath {
        let paced = CommandLine.arguments.contains("--pace")
        do {
            let file = try AVAudioFile(forReading: URL(fileURLWithPath: filePath))
            guard let converter = AVAudioConverter(from: file.processingFormat, to: wanted) else {
                note(["type": "error", "code": "recognition_failed", "detail": "unreadable format"]); return
            }
            note(["type": "ready"])
            while file.framePosition < file.length {
                guard let chunk = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: 8192) else { break }
                try file.read(into: chunk)
                if chunk.frameLength == 0 { break }
                if let converted = convert(converter, chunk) { write(converted) }
                if paced {      // --pace: at the speed it was spoken, like a microphone (tests)
                    try? await Task.sleep(nanoseconds: UInt64(Double(chunk.frameLength) / file.processingFormat.sampleRate * 1_000_000_000))
                }
            }
        } catch {
            note(["type": "error", "code": "recognition_failed", "detail": "\(error)"])
        }
        return
    }
    if CommandLine.arguments.contains("--system") {
        guard let sound = await openSystemSound({ note(["type": "error", "code": $0, "detail": $1]) }) else { return }
        guard let converter = AVAudioConverter(from: sound.format, to: wanted) else {
            note(["type": "error", "code": "system_audio_unavailable", "detail": "format"]); return
        }
        guard sound.start({ buffer in if let converted = convert(converter, buffer) { write(converted) } }) else {
            sound.stop()
            note(["type": "error", "code": "system_audio_unavailable", "detail": "start"]); return
        }
        note(["type": "ready"])
        await waitForStop()
        sound.stop()
        return
    }
    if AVCaptureDevice.authorizationStatus(for: .audio) == .notDetermined {
        _ = await AVCaptureDevice.requestAccess(for: .audio)
    }
    guard AVCaptureDevice.authorizationStatus(for: .audio) == .authorized else {
        note(["type": "error", "code": "microphone_" + microphoneState()]); return
    }
    let engine = AVAudioEngine()
    let input = engine.inputNode
    if let deviceUID, !deviceUID.isEmpty, var device = audioDeviceID(forUID: deviceUID), let unit = input.audioUnit {
        _ = AudioUnitSetProperty(unit, kAudioOutputUnitProperty_CurrentDevice, kAudioUnitScope_Global, 0,
                                 &device, UInt32(MemoryLayout<AudioDeviceID>.size))
    }
    let inputFormat = input.outputFormat(forBus: 0)
    guard inputFormat.sampleRate > 0, let converter = AVAudioConverter(from: inputFormat, to: wanted) else {
        note(["type": "error", "code": "input_device_unusable"]); return
    }
    input.installTap(onBus: 0, bufferSize: 2048, format: inputFormat) { buffer, _ in
        if let converted = convert(converter, buffer) { write(converted) }
    }
    do {
        engine.prepare()
        try engine.start()
    } catch {
        note(["type": "error", "code": "input_device_unusable", "detail": "\(error)"]); return
    }
    note(["type": "ready"])
    await waitForStop()
    input.removeTap(onBus: 0)
    engine.stop()
}

if CommandLine.arguments.contains("--output") {
    runOutput()
    exit(0)
}
if CommandLine.arguments.contains("--capture") {
    await runCapture(deviceUID: argument("--device"), filePath: argument("--file"))
    note(["type": "done"])
    exit(0)
}
if CommandLine.arguments.contains("--check") {
    await runCheck()
} else if CommandLine.arguments.contains("--chat") {
    await runChat()
} else {
    await runListen(localeID: argument("--locale") ?? Locale.current.identifier(.bcp47),
                    deviceUID: argument("--device"), filePath: argument("--file"))
}
emit(["type": "done"])
