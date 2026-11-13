from app.services.metrics import aggregates

def test_empty_data_does_not_invent_rate():
    result=aggregates([])
    assert result['total_kg']==0 and result['recycling_rate'] is None

def test_recycling_is_confirmed_only():
    rows=[{'id':'a','weight_kg':2.5,'single_use':True,'confirmed_recycled_kg':1.0},
          {'id':'b','weight_kg':1.5,'single_use':False,'confirmed_recycled_kg':0}]
    v=aggregates(rows)
    assert v['total_kg']==4 and v['recycling_rate']==25 and v['single_use_pct']==62.5
