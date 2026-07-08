import json

TRAINING_STATUSES = ['not_started', 'in_progress', 'ended', 'archived', 'active']

def validate_training_create(data):
    errors = []
    if not data.get('title'):
        errors.append('title is required')
    if 'title' in data and len(data['title']) > 200:
        errors.append('title max length 200')
    if not data.get('deadline'):
        errors.append('deadline is required')
    if 'status' in data and data['status'] not in TRAINING_STATUSES:
        errors.append('status must be one of ' + ', '.join(TRAINING_STATUSES))
    if 'class_ids' in data and not isinstance(data['class_ids'], list):
        errors.append('class_ids must be a list')
    if 'dimensions' in data and not isinstance(data['dimensions'], list):
        errors.append('dimensions must be a list')
    return not errors, errors or None

def validate_training_update(data):
    errors = []
    if 'title' in data and len(data['title']) > 200:
        errors.append('title max length 200')
    if 'status' in data and data['status'] not in TRAINING_STATUSES:
        errors.append('status must be one of ' + ', '.join(TRAINING_STATUSES))
    if 'class_ids' in data and not isinstance(data['class_ids'], list):
        errors.append('class_ids must be a list')
    if 'dimensions' in data and not isinstance(data['dimensions'], list):
        errors.append('dimensions must be a list')
    return not errors, errors or None

def validate_submission(data):
    errors = []
    if not data.get('training_id'):
        errors.append('training_id is required')
    if not data.get('student_name'):
        errors.append('student_name is required')
    return not errors, errors or None

def validate_indicator_create(data):
    errors = []
    if not data.get('training_id'):
        errors.append('training_id is required')
    if not data.get('name'):
        errors.append('name is required')
    if 'weight' in data and (data['weight'] <= 0 or data['weight'] > 10):
        errors.append('weight must be between 0.1 and 10')
    if 'max_score' in data and data['max_score'] <= 0:
        errors.append('max_score must be positive')
    if 'indicator_type' in data and data['indicator_type'] not in ['auto', 'manual']:
        errors.append('indicator_type must be auto or manual')
    return not errors, errors or None

def validate_teacher_review(data):
    errors = []
    if 'teacher_score' in data:
        if not isinstance(data['teacher_score'], (int, float)):
            errors.append('teacher_score must be a number')
        elif data['teacher_score'] < 0 or data['teacher_score'] > 100:
            errors.append('teacher_score must be between 0 and 100')
    return not errors, errors or None

def validate_llm_config(data):
    errors = []
    if 'provider' in data and data['provider'] not in ['openai', 'ollama']:
        errors.append('provider must be openai or ollama')
    return not errors, errors or None


def validate_system_config(data):
    errors = []
    upload = data.get('upload', {}) or {}
    report = data.get('report', {}) or {}
    switches = data.get('switches', {}) or {}

    if 'upload_max_size_mb' in upload:
        try:
            size = int(upload['upload_max_size_mb'])
            if size < 1 or size > 1024:
                errors.append('upload_max_size_mb must be between 1 and 1024')
        except (TypeError, ValueError):
            errors.append('upload_max_size_mb must be an integer')

    if 'report_template' in report and report['report_template'] not in ['standard', 'compact']:
        errors.append('report_template must be standard or compact')

    for key, value in switches.items():
        if not isinstance(value, bool):
            errors.append(f'{key} must be boolean')

    return not errors, errors or None

def parse_json_field(value, default=None):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    return value

def serialize_json_field(value):
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)