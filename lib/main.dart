import 'dart:io';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import 'api_service.dart';

void main() {
  runApp(const CivicAiApp());
}

class CivicAiApp extends StatelessWidget {
  const CivicAiApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'SahayaNidhi Portal',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF6366F1),
            brightness: Brightness.light,
          ),
          scaffoldBackgroundColor: const Color(0xFFF8FAFC),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF1E293B),
            foregroundColor: Colors.white,
            elevation: 0,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        home: const RoleSelectionScreen(),
      );
}

class RoleSelectionScreen extends StatefulWidget {
  const RoleSelectionScreen({super.key});

  @override
  State<RoleSelectionScreen> createState() => _RoleSelectionScreenState();
}

class _RoleSelectionScreenState extends State<RoleSelectionScreen> {
  String _role = 'Citizen';

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Card(
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Icon(Icons.shield_rounded,
                          size: 52, color: Color(0xFF6366F1)),
                      const SizedBox(height: 12),
                      Text(
                        'SahayaNidhi Civic Portal',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Choose a demo role to continue. Sign-in and identity '
                        'management are not configured in this prototype.',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 20),
                      DropdownButtonFormField<String>(
                        initialValue: _role,
                        decoration: const InputDecoration(labelText: 'Demo role'),
                        items: const [
                          DropdownMenuItem(
                              value: 'Citizen', child: Text('Citizen')),
                          DropdownMenuItem(
                              value: 'Field Worker',
                              child: Text('Field Worker')),
                          DropdownMenuItem(
                              value: 'Commissioner',
                              child: Text('High Commissioner')),
                        ],
                        onChanged: (value) {
                          if (value != null) setState(() => _role = value);
                        },
                      ),
                      const SizedBox(height: 18),
                      FilledButton(
                        onPressed: () => Navigator.of(context).pushReplacement(
                          MaterialPageRoute<void>(
                            builder: (_) => MainShell(userRole: _role),
                          ),
                        ),
                        child: const Text('Continue to demo'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );
}

class MainShell extends StatefulWidget {
  const MainShell({super.key, required this.userRole});

  final String userRole;

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  final _tokenIdController = TextEditingController();

  @override
  void dispose() {
    _tokenIdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Widget screen;
    switch (widget.userRole) {
      case 'Citizen':
        screen = CitizenScreen(onTokenCreated: _setTokenId);
        break;
      case 'Field Worker':
        screen = WorkerScreen(tokenIdController: _tokenIdController);
        break;
      default:
        screen = CommissionerScreen(
          tokenIdController: _tokenIdController,
          onSelectToken: _setTokenId,
        );
        break;
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('SahayaNidhi · ${widget.userRole}'),
        actions: [
          IconButton(
            tooltip: 'Change demo role',
            icon: const Icon(Icons.logout_rounded),
            onPressed: () => Navigator.of(context).pushReplacement(
              MaterialPageRoute<void>(
                  builder: (_) => const RoleSelectionScreen()),
            ),
          ),
        ],
      ),
      body: screen,
    );
  }

  void _setTokenId(String tokenId) {
    _tokenIdController.text = tokenId;
  }
}

class CitizenScreen extends StatefulWidget {
  const CitizenScreen({super.key, required this.onTokenCreated});

  final ValueChanged<String> onTokenCreated;

  @override
  State<CitizenScreen> createState() => _CitizenScreenState();
}

class _CitizenScreenState extends State<CitizenScreen> {
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _latitudeController = TextEditingController(text: '12.97160');
  final _longitudeController = TextEditingController(text: '77.59460');
  final _picker = ImagePicker();
  String _category = 'other';
  String? _photoPath;
  String? _message;
  bool _busy = false;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    super.dispose();
  }

  Future<void> _captureLocation() async {
    try {
      final position = await _currentPosition();
      if (!mounted) return;
      setState(() {
        _latitudeController.text = position.latitude.toStringAsFixed(6);
        _longitudeController.text = position.longitude.toStringAsFixed(6);
      });
    } catch (error) {
      _showMessage('Could not get location: $error');
    }
  }

  Future<void> _pickPhoto() async {
    try {
      final photo = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
      );
      if (photo != null && mounted) setState(() => _photoPath = photo.path);
    } catch (error) {
      _showMessage('Could not open the camera: $error');
    }
  }

  Future<void> _submit() async {
    final description = _descriptionController.text.trim();
    final latitude = double.tryParse(_latitudeController.text.trim());
    final longitude = double.tryParse(_longitudeController.text.trim());
    if (description.length < 5 || latitude == null || longitude == null) {
      _showMessage('Enter a description of at least 5 characters and valid coordinates.');
      return;
    }

    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      final result = await CivicApi.instance.createToken(
        fields: {
          'description': description,
          'declared_category': _category,
          'latitude': '$latitude',
          'longitude': '$longitude',
          'citizen_reference': _nameController.text.trim().isEmpty
              ? 'demo-anonymous'
              : _nameController.text.trim(),
        },
        photoPath: _photoPath,
      );
      final token = Map<String, dynamic>.from(result['token'] as Map);
      final tokenId = token['token_id'] as String;
      widget.onTokenCreated(tokenId);
      if (!mounted) return;
      setState(() {
        _message = 'Report submitted.\nToken: $tokenId\n'
            'Status: ${token['status']} · ${token['severity_level']}';
        _descriptionController.clear();
        _photoPath = null;
      });
    } catch (error) {
      _showMessage('Report failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const _InfoCard(
            text: 'Use synthetic reports only. Your report is sent to the '
                'configured SahayaNidhi backend for classification and duplicate checks.',
          ),
          const SizedBox(height: 14),
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(labelText: 'Demo citizen reference'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _category,
            decoration: const InputDecoration(labelText: 'Issue category'),
            items: const [
              DropdownMenuItem(value: 'other', child: Text('Let intake classify')),
              DropdownMenuItem(value: 'open_drain', child: Text('Open drain')),
              DropdownMenuItem(value: 'pothole', child: Text('Pothole')),
              DropdownMenuItem(value: 'streetlight', child: Text('Streetlight')),
              DropdownMenuItem(value: 'water_leak', child: Text('Water leak')),
              DropdownMenuItem(value: 'fallen_tree', child: Text('Fallen tree')),
            ],
            onChanged: (value) {
              if (value != null) setState(() => _category = value);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _descriptionController,
            minLines: 2,
            maxLines: 4,
            maxLength: 1000,
            decoration: const InputDecoration(labelText: 'Description'),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _latitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: const InputDecoration(labelText: 'Latitude'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _longitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: const InputDecoration(labelText: 'Longitude'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: _busy ? null : _captureLocation,
            icon: const Icon(Icons.my_location),
            label: const Text('Use current location'),
          ),
          OutlinedButton.icon(
            onPressed: _busy ? null : _pickPhoto,
            icon: const Icon(Icons.camera_alt_outlined),
            label: Text(_photoPath == null ? 'Take before photo' : 'Photo attached'),
          ),
          if (_photoPath != null) ...[
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.file(File(_photoPath!), height: 180, fit: BoxFit.cover),
            ),
          ],
          const SizedBox(height: 14),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Submitting…' : 'Submit grievance'),
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            SelectableText(_message!),
          ],
        ],
      );

  void _showMessage(String message) {
    if (mounted) setState(() => _message = message);
  }
}

class WorkerScreen extends StatefulWidget {
  const WorkerScreen({super.key, required this.tokenIdController});

  final TextEditingController tokenIdController;

  @override
  State<WorkerScreen> createState() => _WorkerScreenState();
}

class _WorkerScreenState extends State<WorkerScreen> {
  final _notesController = TextEditingController();
  final _latitudeController = TextEditingController(text: '12.97160');
  final _longitudeController = TextEditingController(text: '77.59460');
  final _picker = ImagePicker();
  List<Map<String, dynamic>> _workers = [];
  String? _workerId;
  String? _photoPath;
  String? _message;
  bool _attested = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadWorkers();
  }

  @override
  void dispose() {
    _notesController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    super.dispose();
  }

  Future<void> _loadWorkers() async {
    try {
      final result = await CivicApi.instance.workers();
      if (!mounted) return;
      setState(() {
        _workers = List<Map<String, dynamic>>.from(result['items'] as List);
        if (_workers.isNotEmpty && !_workers.any((w) => w['worker_id'] == _workerId)) {
          _workerId = _workers.first['worker_id'] as String;
        }
      });
    } catch (error) {
      _showMessage('Could not load workers: $error');
    }
  }

  Future<void> _startWork() async {
    final tokenId = widget.tokenIdController.text.trim();
    final workerId = _workerId;
    if (tokenId.isEmpty || workerId == null) {
      _showMessage('Enter a token ID and select a worker.');
      return;
    }
    await _runAction(
      () => CivicApi.instance.startWork(tokenId, workerId),
      'Work started.',
    );
  }

  Future<void> _submitProof() async {
    final tokenId = widget.tokenIdController.text.trim();
    final workerId = _workerId;
    final latitude = double.tryParse(_latitudeController.text.trim());
    final longitude = double.tryParse(_longitudeController.text.trim());
    if (tokenId.isEmpty || workerId == null || _photoPath == null || !_attested) {
      _showMessage(
        'Enter a token ID, select a worker, attach an after photo, and confirm the attestation.',
      );
      return;
    }
    if (_notesController.text.trim().length < 10 ||
        latitude == null ||
        longitude == null) {
      _showMessage('Add 10+ characters of notes and valid worker coordinates.');
      return;
    }

    await _runAction(
      () => CivicApi.instance.submitRepairProof(
        tokenId: tokenId,
        fields: {
          'worker_id': workerId,
          'worker_latitude': '$latitude',
          'worker_longitude': '$longitude',
          'notes': _notesController.text.trim(),
          'worker_attested_repaired': '$_attested',
        },
        photoPath: _photoPath!,
      ),
      'Repair proof submitted.',
    );
  }

  Future<void> _runAction(
    Future<Map<String, dynamic>> Function() action,
    String successMessage,
  ) async {
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      final result = await action();
      final token = result['token'];
      final tokenData = token is Map ? Map<String, dynamic>.from(token) : result;
      if (!mounted) return;
      setState(() {
        _message = '$successMessage\nStatus: ${tokenData['status'] ?? 'updated'}'
            '${result['verification'] is Map ? '\nVerification: ${(result['verification'] as Map)['status']}' : ''}';
        if (result.containsKey('verification')) {
          _photoPath = null;
          _attested = false;
        }
      });
    } catch (error) {
      _showMessage('Request failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _captureLocation() async {
    try {
      final position = await _currentPosition();
      if (!mounted) return;
      setState(() {
        _latitudeController.text = position.latitude.toStringAsFixed(6);
        _longitudeController.text = position.longitude.toStringAsFixed(6);
      });
    } catch (error) {
      _showMessage('Could not get location: $error');
    }
  }

  Future<void> _pickPhoto() async {
    try {
      final photo = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
      );
      if (photo != null && mounted) setState(() => _photoPath = photo.path);
    } catch (error) {
      _showMessage('Could not open the camera: $error');
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const _InfoCard(
            text: 'Select a worker already assigned to this token. Start the '
                'work before submitting repair evidence.',
          ),
          const SizedBox(height: 14),
          TextField(
            controller: widget.tokenIdController,
            decoration: const InputDecoration(labelText: 'Token ID'),
          ),
          const SizedBox(height: 12),
          if (_workers.isEmpty)
            const LinearProgressIndicator()
          else
            DropdownButtonFormField<String>(
              initialValue: _workerId,
              decoration: const InputDecoration(labelText: 'Assigned worker'),
              items: _workers
                  .map((worker) => DropdownMenuItem(
                        value: worker['worker_id'] as String,
                        child: Text(
                          '${worker['worker_id']} · ${worker['name']} (${worker['zone']})',
                        ),
                      ))
                  .toList(),
              onChanged: (value) => setState(() => _workerId = value),
            ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _busy ? null : _startWork,
            child: const Text('Start assigned work'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notesController,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Completion notes (at least 10 characters)',
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _latitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: const InputDecoration(labelText: 'Worker latitude'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _longitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: const InputDecoration(labelText: 'Worker longitude'),
                ),
              ),
            ],
          ),
          OutlinedButton.icon(
            onPressed: _busy ? null : _captureLocation,
            icon: const Icon(Icons.my_location),
            label: const Text('Use current location'),
          ),
          OutlinedButton.icon(
            onPressed: _busy ? null : _pickPhoto,
            icon: const Icon(Icons.camera_alt_outlined),
            label: Text(_photoPath == null ? 'Take after photo' : 'Photo attached'),
          ),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: _attested,
            onChanged: _busy
                ? null
                : (value) => setState(() => _attested = value ?? false),
            title: const Text('I attest that the repair work is complete'),
          ),
          if (_photoPath != null) ...[
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.file(File(_photoPath!), height: 180, fit: BoxFit.cover),
            ),
          ],
          const SizedBox(height: 12),
          FilledButton(
            onPressed: _busy ? null : _submitProof,
            child: Text(_busy ? 'Submitting…' : 'Submit repair proof'),
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            SelectableText(_message!),
          ],
        ],
      );

  void _showMessage(String message) {
    if (mounted) setState(() => _message = message);
  }
}

class CommissionerScreen extends StatefulWidget {
  const CommissionerScreen({
    super.key,
    required this.tokenIdController,
    required this.onSelectToken,
  });

  final TextEditingController tokenIdController;
  final ValueChanged<String> onSelectToken;

  @override
  State<CommissionerScreen> createState() => _CommissionerScreenState();
}

class _CommissionerScreenState extends State<CommissionerScreen> {
  Map<String, dynamic>? _dashboard;
  List<Map<String, dynamic>> _tokens = [];
  List<Map<String, dynamic>> _workers = [];
  String? _workerId;
  String? _details;
  String? _message;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _busy = true);
    try {
      final dashboard = await CivicApi.instance.dashboard();
      final tokens = await CivicApi.instance.tokens();
      final workers = await CivicApi.instance.workers();
      if (!mounted) return;
      setState(() {
        _dashboard = dashboard;
        _tokens = List<Map<String, dynamic>>.from(tokens['items'] as List);
        _workers = List<Map<String, dynamic>>.from(workers['items'] as List);
        if (_workers.isNotEmpty &&
            !_workers.any((worker) => worker['worker_id'] == _workerId)) {
          _workerId = _workers.first['worker_id'] as String;
        }
        _message = null;
      });
    } catch (error) {
      _showMessage('Could not load dashboard: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _assign() async {
    final tokenId = widget.tokenIdController.text.trim();
    final workerId = _workerId;
    if (tokenId.isEmpty || workerId == null) {
      _showMessage('Select a token and worker before assigning.');
      return;
    }
    await _runAction(
      () => CivicApi.instance.assignToken(tokenId, workerId),
      'Token assigned.',
    );
  }

  Future<void> _runAction(
    Future<Map<String, dynamic>> Function() action,
    String successMessage,
  ) async {
    setState(() => _busy = true);
    try {
      await action();
      if (!mounted) return;
      setState(() => _message = successMessage);
      await _refresh();
    } catch (error) {
      _showMessage('Request failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _showDetails(String tokenId) async {
    widget.onSelectToken(tokenId);
    try {
      final details = await CivicApi.instance.token(tokenId);
      if (mounted) setState(() => _details = details.toString());
    } catch (error) {
      _showMessage('Could not load token details: $error');
    }
  }

  Future<void> _runDemoAction(
    Future<Map<String, dynamic>> Function() action,
  ) async {
    await _runAction(action, 'Demo operation completed.');
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const _InfoCard(
              text: 'Operations and records are loaded from the connected '
                  'backend. Demo actions create synthetic records.',
            ),
            const SizedBox(height: 14),
            if (_dashboard != null) _buildStats(),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  onPressed: _busy ? null : _refresh,
                  child: const Text('Refresh'),
                ),
                OutlinedButton(
                  onPressed: _busy
                      ? null
                      : () => _runDemoAction(CivicApi.instance.seedDemo),
                  child: const Text('Seed demo cases'),
                ),
                OutlinedButton(
                  onPressed: _busy
                      ? null
                      : () => _runDemoAction(CivicApi.instance.checkSla),
                  child: const Text('Check SLA now'),
                ),
              ],
            ),
            if (_message != null) ...[
              const SizedBox(height: 10),
              SelectableText(_message!),
            ],
            const SizedBox(height: 12),
            const Text('Tokens', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            if (_tokens.isEmpty && !_busy)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Text('No tokens yet. Submit a report or seed demo cases.'),
              ),
            ..._tokens.map(_buildTokenCard),
            if (_workers.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Assign selected token',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              TextField(
                controller: widget.tokenIdController,
                decoration: const InputDecoration(labelText: 'Token ID'),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _workerId,
                decoration: const InputDecoration(labelText: 'Worker'),
                items: _workers
                    .map((worker) => DropdownMenuItem(
                          value: worker['worker_id'] as String,
                          child: Text(
                            '${worker['worker_id']} · ${worker['name']}',
                          ),
                        ))
                    .toList(),
                onChanged: (value) => setState(() => _workerId = value),
              ),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: _busy ? null : _assign,
                child: const Text('Assign token'),
              ),
            ],
            if (_details != null) ...[
              const SizedBox(height: 12),
              const Text('Selected token and audit details',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              SelectableText(_details!),
            ],
          ],
        ),
      );

  Widget _buildStats() {
    final dashboard = _dashboard!;
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Wrap(
          spacing: 16,
          runSpacing: 10,
          children: [
            _Stat(label: 'Work orders', value: '${dashboard['total_work_orders']}'),
            _Stat(label: 'SLA breached', value: '${dashboard['overdue']}'),
            _Stat(label: 'Duplicate reports', value: '${dashboard['duplicate_reports']}'),
          ],
        ),
      ),
    );
  }

  Widget _buildTokenCard(Map<String, dynamic> token) {
    final tokenId = token['token_id'] as String;
    return Card(
      color: Colors.white,
      child: ListTile(
        title: Text('${token['category']} · ${token['severity_level']}'),
        subtitle: Text(
          '${token['status']} · ${token['assigned_worker_id'] ?? 'Unassigned'}\n$tokenId',
        ),
        isThreeLine: true,
        onTap: () => _showDetails(tokenId),
        trailing: IconButton(
          tooltip: 'Select token for assignment',
          icon: const Icon(Icons.assignment_ind_outlined),
          onPressed: () => widget.onSelectToken(tokenId),
        ),
      ),
    );
  }

  void _showMessage(String message) {
    if (mounted) setState(() => _message = message);
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold)),
          Text(label),
        ],
      );
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFFEEF2FF),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Text(text, style: const TextStyle(color: Color(0xFF3730A3))),
        ),
      );
}

Future<Position> _currentPosition() async {
  if (!await Geolocator.isLocationServiceEnabled()) {
    throw const FormatException('Location services are disabled.');
  }
  var permission = await Geolocator.checkPermission();
  if (permission == LocationPermission.denied) {
    permission = await Geolocator.requestPermission();
  }
  if (permission == LocationPermission.denied ||
      permission == LocationPermission.deniedForever) {
    throw const FormatException('Location permission was not granted.');
  }
  return Geolocator.getCurrentPosition(
    locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
  );
}
