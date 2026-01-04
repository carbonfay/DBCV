# Инструкция по запуску тестов

## Подготовка окружения
1. Установите Miniconda и создайте/обновите окружение:
   ```bash
   conda env create -f environment.yml
   # или, если окружение уже есть
   conda activate DBCV
   conda run -n DBCV pip install -r backend/requirements.txt
   ```
2. Перед запуском убедитесь, что активировано окружение `DBCV`:
   ```bash
   conda activate DBCV
   ```
3. Для тестов, требующих токены, установите переменные окружения:
   ```bash
   # CMS provider-data API (для get_pharmacy_info и search_pharmacies)
   export MEDICINE_APP_TOKEN=<X-App-Token>
   
   # WHO ICD API (для get_disease_info)
   export WHO_ICD_API_TOKEN=<Bearer_Token>
   
   # Infermedica API (для get_symptoms)
   export INFERMEDICA_APP_ID=<App-Id>
   export INFERMEDICA_APP_KEY=<App-Key>
   ```

## Запуск всех интеграционных тестов medicine
```bash
cd backend
conda run -n DBCV python -m pytest app/tests/integrations/test_medicine_*.py -v --noconftest
```

## Запуск только тестов с реальными API вызовами
```bash
cd backend
conda run -n DBCV python -m pytest app/tests/integrations/test_medicine_*.py -v --noconftest -k "test_execute_real"
```

## Запуск конкретного теста
```bash
cd backend
conda run -n DBCV python -m pytest app/tests/integrations/test_medicine_search_drugs.py::test_execute_real_rxnav -v --noconftest
```

## Тесты с реальными API вызовами

Все интеграции имеют тесты с реальными вызовами к API:

### Публичные API (без токенов)
- `test_medicine_get_articles.py::test_execute_real_pubmed` - PubMed (NCBI)
- `test_medicine_get_atc_code.py::test_execute_real_rxnav` - RxNav (NLM)
- `test_medicine_get_drug_info.py::test_execute_real_rxnav` - RxNav (NLM)
- `test_medicine_get_drug_interactions.py::test_execute_real_rxnav` - openFDA
- `test_medicine_get_hospital_info.py::test_execute_real_medicare` - CMS provider-data
- `test_medicine_get_icd10.py::test_execute_real_clinicaltables` - ClinicalTables (NLM)
- `test_medicine_get_trials.py::test_execute_real_clinicaltrials` - ClinicalTrials.gov
- `test_medicine_search_diseases.py::test_execute_real_clinicaltables` - ClinicalTables (NLM)
- `test_medicine_search_doctors.py::test_execute_real_npi_registry` - NPI Registry (CMS)
- `test_medicine_get_doctor_info.py::test_execute_real_npi_registry` - NPI Registry (CMS)
- `test_medicine_search_drugs.py::test_execute_real_rxnav` - RxNav (NLM)

### API с токенами (требуют переменные окружения)
- `test_medicine_get_pharmacy_info.py::test_execute_real_cms` - CMS provider-data (требует `MEDICINE_APP_TOKEN`)
- `test_medicine_search_pharmacies.py::test_execute_real_socrata` - CMS provider-data (требует `MEDICINE_APP_TOKEN`)
- `test_medicine_get_disease_info.py::test_execute_real_who_icd` - WHO ICD API (требует `WHO_ICD_API_TOKEN`)
- `test_medicine_get_symptoms.py::test_execute_real_infermedica` - Infermedica API (требует `INFERMEDICA_APP_ID` и `INFERMEDICA_APP_KEY`)

## Логи реальных вызовов
- Результаты реальных запросов сохраняются в `backend/app/tests/integrations/logs/` с именами вида `<файл_теста>_<дата_время>_<имя_теста>.json`.
- Если реальный вызов недоступен (сетевой недоступ, 404 от публичного API), лог поможет диагностировать причину.
- Тесты с токенами автоматически пропускаются (`SKIPPED`), если переменные окружения не установлены.
