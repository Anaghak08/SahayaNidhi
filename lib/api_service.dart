import 'dart:convert';
import 'dart:io';

class CivicApi {
  CivicApi._() : _client = HttpClient() {
    final configuredUrl = const String.fromEnvironment('API_BASE_URL');
    final defaultUrl = Platform.isAndroid
        ? 'http://10.0.2.2:8000'
        : 'http://127.0.0.1:8000';
    _baseUri = Uri.parse(configuredUrl.isEmpty ? defaultUrl : configuredUrl);
  }

  static final CivicApi instance = CivicApi._();
  static const _timeout = Duration(seconds: 20);
  final HttpClient _client;
  late final Uri _baseUri;

  Uri _uri(String path) => _baseUri.resolve(path);

  Future<Map<String, dynamic>> get(String path) async {
    final request = await _client.getUrl(_uri(path)).timeout(_timeout);
    return _send(request);
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, Object?> body,
  ) async {
    final request = await _client.postUrl(_uri(path)).timeout(_timeout);
    request.headers.contentType = ContentType.json;
    request.write(jsonEncode(body));
    return _send(request);
  }

  Future<Map<String, dynamic>> createToken({
    required Map<String, String> fields,
    String? photoPath,
  }) =>
      _postMultipart('/api/tokens', fields, 'before_photo', photoPath);

  Future<Map<String, dynamic>> submitRepairProof({
    required String tokenId,
    required Map<String, String> fields,
    required String photoPath,
  }) =>
      _postMultipart(
        '/api/tokens/${Uri.encodeComponent(tokenId)}/repair-proof',
        fields,
        'after_photo',
        photoPath,
      );

  Future<Map<String, dynamic>> _postMultipart(
    String path,
    Map<String, String> fields,
    String fileField,
    String? filePath,
  ) async {
    final boundary = 'civic-${DateTime.now().microsecondsSinceEpoch}';
    final request = await _client.postUrl(_uri(path)).timeout(_timeout);
    request.headers.set(
      HttpHeaders.contentTypeHeader,
      'multipart/form-data; boundary=$boundary',
    );

    void addText(String value) => request.add(utf8.encode(value));

    for (final entry in fields.entries) {
      addText('--$boundary\r\n'
          'Content-Disposition: form-data; name="${entry.key}"\r\n\r\n'
          '${entry.value}\r\n');
    }

    if (filePath != null) {
      final file = File(filePath);
      final fileName =
          file.uri.pathSegments.last.replaceAll(RegExp(r'[\r\n"\\]'), '_');
      final mediaType = _imageMediaType(fileName);
      final bytes = await file.readAsBytes();
      addText('--$boundary\r\n'
          'Content-Disposition: form-data; name="$fileField"; '
          'filename="$fileName"\r\n'
          'Content-Type: $mediaType\r\n\r\n');
      request.add(bytes);
      addText('\r\n');
    }
    addText('--$boundary--\r\n');
    return _send(request);
  }

  String _imageMediaType(String fileName) {
    final extension = fileName.split('.').last.toLowerCase();
    return switch (extension) {
      'jpg' || 'jpeg' => 'image/jpeg',
      'png' => 'image/png',
      'webp' => 'image/webp',
      _ => throw FormatException('Unsupported image format: $extension'),
    };
  }

  Future<Map<String, dynamic>> _send(HttpClientRequest request) async {
    final response = await request.close().timeout(_timeout);
    final body = await utf8.decoder.bind(response).join().timeout(_timeout);
    final decoded = jsonDecode(body);
    if (decoded is! Map) {
      throw const FormatException('Backend returned an invalid response.');
    }

    final result = Map<String, dynamic>.from(decoded);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = result['detail'];
      throw CivicApiException(
        detail is String ? detail : 'Request failed (${response.statusCode}).',
      );
    }
    return result;
  }

  Future<Map<String, dynamic>> dashboard() => get('/api/dashboard');
  Future<Map<String, dynamic>> tokens() => get('/api/tokens');
  Future<Map<String, dynamic>> workers() => get('/api/workers');
  Future<Map<String, dynamic>> token(String tokenId) =>
      get('/api/tokens/${Uri.encodeComponent(tokenId)}');

  Future<Map<String, dynamic>> assignToken(
    String tokenId,
    String workerId,
  ) =>
      postJson('/api/tokens/${Uri.encodeComponent(tokenId)}/assign', {
        'worker_id': workerId,
      });

  Future<Map<String, dynamic>> startWork(
    String tokenId,
    String workerId,
  ) =>
      postJson('/api/tokens/${Uri.encodeComponent(tokenId)}/start', {
        'worker_id': workerId,
      });

  Future<Map<String, dynamic>> seedDemo() =>
      postJson('/api/demo/seed', const {});

  Future<Map<String, dynamic>> checkSla() =>
      postJson('/api/demo/check-sla', const {});
}

class CivicApiException implements Exception {
  const CivicApiException(this.message);

  final String message;

  @override
  String toString() => message;
}
