from pathlib import Path
from app.java_analysis import analyze_java_repository

def test_java_parser_extracts_spring_kafka_and_sql(tmp_path: Path):
    p=tmp_path/"src/main/java/demo/Worker.java"; p.parent.mkdir(parents=True)
    p.write_text('''package demo;
import org.springframework.kafka.annotation.KafkaListener;
class Worker {
 @KafkaListener(topics = "billing.data")
 public void consume(String value) {
  if (value == null) throw new IllegalArgumentException();
  repository.save(value);
 }
}''',encoding="utf-8")
    q=tmp_path/"src/main/resources/query.sql"; q.parent.mkdir(parents=True)
    q.write_text("SELECT * FROM BILLING; UPDATE BILLING SET STATUS='DONE';",encoding="utf-8")
    result=analyze_java_repository(tmp_path)
    assert any(x["name"]=="Worker" for x in result["classes"])
    assert any(x["name"]=="consume" for x in result["methods"])
    assert result["kafka_listeners"]
    assert len(result["sql_statements"])>=2
