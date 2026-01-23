class ApiError implements Exception {
  ApiError({
    required this.code,
    required this.message,
    required this.requestId,
  });

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
    required this.status,
    required this.sanitizedText,
    required this.riskLevel,
    required this.reidRisk,
    required this.identityLeak,
    required this.leakTypes,
    required this.crisisAction,
  });

  final String status;
  final String? sanitizedText;
  final int riskLevel;
  final double reidRisk;
  final bool identityLeak;
  final List<String> leakTypes;
  final String? crisisAction;

  factory MoodResponse.fromJson(Map<String, dynamic> json) {
    return MoodResponse(
      status: json['status'] as String? ?? 'ok',
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
  MatchCandidate({
    required this.candidateId,
    required this.intensity,
    required this.themes,
  });

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

class InboxItem {
  InboxItem({
    required this.inboxItemId,
    required this.text,
    required this.receivedAt,
    required this.ackStatus,
  });

  final String inboxItemId;
  final String text;
  final String receivedAt;
  final String? ackStatus;

  factory InboxItem.fromJson(Map<String, dynamic> json) {
    return InboxItem(
      inboxItemId: json['inbox_item_id'] as String? ?? '',
      text: json['text'] as String? ?? '',
      receivedAt:
          json['created_at'] as String? ?? json['received_at'] as String? ?? '',
      ackStatus: json['ack_status'] as String?,
    );
  }
}

class InboxResponse {
  InboxResponse({required this.items, required this.nextCursor});

  final List<InboxItem> items;
  final String? nextCursor;

  factory InboxResponse.fromJson(Map<String, dynamic> json) {
    return InboxResponse(
      items: (json['items'] as List<dynamic>? ?? [])
          .map((item) => InboxItem.fromJson(item as Map<String, dynamic>))
          .toList(),
      nextCursor: json['next_cursor'] as String?,
    );
  }
}

class AcknowledgementRequest {
  AcknowledgementRequest({required this.inboxItemId, required this.reaction});

  final String inboxItemId;
  final String reaction;

  Map<String, dynamic> toJson() {
    return {'inbox_item_id': inboxItemId, 'reaction': reaction};
  }
}

class AcknowledgementResponse {
  AcknowledgementResponse({required this.status});

  final String status;

  factory AcknowledgementResponse.fromJson(Map<String, dynamic> json) {
    return AcknowledgementResponse(
      status: json['status'] as String? ?? 'unknown',
    );
  }
}

class ReflectionSummary {
  ReflectionSummary({
    required this.windowDays,
    required this.totalEntries,
    required this.distribution,
    required this.trend,
    required this.volatilityDays,
  });

  final int windowDays;
  final int totalEntries;
  final Map<String, int> distribution;
  final String trend;
  final int volatilityDays;

  factory ReflectionSummary.fromJson(Map<String, dynamic> json) {
    final rawDistribution =
        (json['distribution'] as Map<String, dynamic>? ?? {});
    return ReflectionSummary(
      windowDays: json['window_days'] as int? ?? 7,
      totalEntries: json['total_entries'] as int? ?? 0,
      distribution: rawDistribution.map(
        (key, value) => MapEntry(key, (value as num?)?.toInt() ?? 0),
      ),
      trend: json['trend'] as String? ?? 'stable',
      volatilityDays: json['volatility_days'] as int? ?? 0,
    );
  }
}

class ImpactResponse {
  ImpactResponse({required this.helpedCount});

  final int helpedCount;

  factory ImpactResponse.fromJson(Map<String, dynamic> json) {
    return ImpactResponse(helpedCount: json['helped_count'] as int? ?? 0);
  }
}
