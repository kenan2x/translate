from app.services.glossary import GlossaryService


def test_from_csv():
    csv_content = """source_term,target_term,do_not_translate
journal,journal,true
pool,havuz,false
fabric,yapi,false"""
    svc = GlossaryService.from_csv(csv_content)
    assert len(svc.terms) == 3
    assert svc.terms[0]["source"] == "journal"
    assert svc.terms[0]["do_not_translate"] is True


def test_prompt_injection():
    svc = GlossaryService([
        {"source": "LDEV", "target": "", "do_not_translate": True},
        {"source": "pool", "target": "havuz", "do_not_translate": False},
    ])
    prompt = svc.get_prompt_injection()
    assert "LDEV" in prompt
    assert "DO NOT TRANSLATE" in prompt
    assert "havuz" in prompt


def test_empty_glossary():
    svc = GlossaryService()
    assert svc.get_prompt_injection() == ""
    assert svc.terms == []


def test_add_term():
    svc = GlossaryService()
    svc.add_term("HUR", "HUR", do_not_translate=True)
    assert len(svc.terms) == 1
    assert svc.terms[0]["source"] == "HUR"


def test_to_csv():
    svc = GlossaryService([
        {"source": "GAD", "target": "GAD", "do_not_translate": True},
    ])
    csv_out = svc.to_csv()
    assert "GAD" in csv_out
    assert "source_term" in csv_out
    assert "true" in csv_out


def test_roundtrip_csv():
    original = GlossaryService([
        {"source": "fabric", "target": "yapi", "do_not_translate": False},
        {"source": "LDEV", "target": "LDEV", "do_not_translate": True},
    ])
    csv_out = original.to_csv()
    restored = GlossaryService.from_csv(csv_out)
    assert len(restored.terms) == 2
    assert restored.terms[0]["source"] == "fabric"
