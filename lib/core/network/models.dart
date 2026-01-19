class ApiError implements Exception {
  ApiError({required this.code, required this.message, required this.requestId});

  final String code;
  final String message;
  final String requestId;

  @override
  String toString() => 'ApiError($code, $message, $requestId)';
}

class MoodRequest {
  MoodRequest({
    required this.valence,
    required this.intensity,
    this.emotion,
    this.freeText,
  });

  final String valence;
  final String intensity;
  final String? emotion;
  final String? freeText;

  Map<String, dynamic> toJson() {
    return {
      'valence': valence,
      'intensity': intensity,
      if (emotion != null) 'emotion': emotion,
      if (freeText != null && freeText!.isNotEmpty) 'free_text': freeText,
    };
  }
}

class MoodResponse {
  MoodResponse({
    required this.sanitizedText,
    required this.riskLevel,
    required this.reidRisk,
    required this.identityLeak,
    required this.leakTypes,
    required this.crisisAction,
  });

  final String? sanitizedText;
  final int riskLevel;
  final double reidRisk;
  final bool identityLeak;
  final List<String> leakTypes;
  final String? crisisAction;

  factory MoodResponse.fromJson(Map<String, dynamic> json) {
    return MoodResponse(
      sanitizedText: json['sanitized_text'] as String?,
      riskLevel: json['risk_level'] as int? ?? 0,
      reidRisk: (json['reid_risk'] as num?)?.toDouble() ?? 0,
      identityLeak: json['identity_leak'] as bool? ?? false,
      leakTypes: (json['leak_types'] as List<dynamic>? ?? [])
          .map((item) => item.toString())
          .toList(),
      crisisAction: json['crisis_action'] as String?,
    );
  }
}

class MatchCandidate {
  MatchCandidate({required this.candidateId, required this.intensity, required this.themes});

  final String candidateId;
  final String intensity;
  final List<String> themes;

  Map<String, dynamic> toJson() {
    return {
      'candidate_id': candidateId,
      'intensity': intensity,
      'themes': themes,
    };
  }
}

class MatchSimulateRequest {
  MatchSimulateRequest({
    required this.riskLevel,
    required this.intensity,
    required this.themes,
    required this.candidates,
  });

  final int riskLevel;
  final String intensity;
  final List<String> themes;
  final List<MatchCandidate> candidates;

  Map<String, dynamic> toJson() {
    return {
      'risk_level': riskLevel,
      'intensity': intensity,
      'themes': themes,
      'candidates': candidates.map((item) => item.toJson()).toList(),
    };
  }
}

class MatchSimulateResponse {
  MatchSimulateResponse({
    required this.decision,
    required this.reason,
    this.systemGeneratedEmpathy,
    this.finiteContentBridge,
  });

  final String decision;
  final String reason;
  final String? systemGeneratedEmpathy;
  final String? finiteContentBridge;

  factory MatchSimulateResponse.fromJson(Map<String, dynamic> json) {
    return MatchSimulateResponse(
      decision: json['decision'] as String? ?? 'UNKNOWN',
      reason: json['reason'] as String? ?? 'unknown',
      systemGeneratedEmpathy: json['system_generated_empathy'] as String?,
      finiteContentBridge: json['finite_content_bridge'] as String?,
    );
  }
}
