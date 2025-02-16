from flask import Flask, request, render_template  # นำเข้า Flask สำหรับการสร้างเว็บแอปพลิเคชัน และ request สำหรับการรับข้อมูลจากผู้ใช้, render_template สำหรับการเรนเดอร์ HTML
from rdflib import Graph, URIRef, Namespace, Literal  # นำเข้า rdflib สำหรับการจัดการ RDF graph และการทำงานกับ data ในรูปแบบ RDF

app = Flask(__name__)  # สร้างแอปพลิเคชัน Flask

g = Graph()  # สร้าง RDF graph
g.parse('mytourism.owl', format='xml')  # โหลดข้อมูลจากไฟล์ RDF ที่ชื่อว่า 'mytourism.owl' ด้วยรูปแบบ XML

# สร้าง namespace สำหรับใช้อ้างอิง predicates ใน RDF
ns = Namespace("http://www.my_ontology.edu/mytourism#")

# คำแปลของ Predicate ตามภาษา
predicate_translations = {
    'hasFlower': {'th': 'ดอกไม้ประจำจังหวัด', 'en': 'Flower'},
    'hasImageOfProvince': {'th': 'รูปภาพของจังหวัด', 'en': 'Image Of Province'},
    'hasLatitudeOfProvince': {'th': 'ละติจูดของจังหวัด', 'en': 'Latitude'},
    'hasLongitudeOfProvince': {'th': 'ลองจิจูดของจังหวัด', 'en': 'Longitude'},
    'hasMotto': {'th': 'คำขวัญของจังหวัด', 'en': 'Motto'},
    'hasNameOfProvince': {'th': 'ชื่อจังหวัด', 'en': 'Name Of Province'},
    'hasSeal': {'th': 'สัญลักษณ์ประจำจังหวัด', 'en': 'Seal'},
    'hasTraditionalNameOfProvince': {'th': 'ชื่อเดิมของจังหวัด', 'en': 'Traditional Name Of Province'},
    'hasTree': {'th': 'ต้นไม้ประจำจังหวัด', 'en': 'Tree'},
    'hasURLOfProvince': {'th': 'เว็บไซต์ของจังหวัด', 'en': 'URL Of Province'}
}

@app.route('/', methods=['GET', 'POST'])  # กำหนด route สำหรับหน้าหลัก โดยรองรับการเรียกผ่าน GET และ POST
def search_province():
    results = set()  # ใช้ set เพื่อป้องกันการซ้ำของผลลัพธ์
    province_name = ""  # ตัวแปรสำหรับเก็บชื่อจังหวัดที่ค้นพบ
    lang = request.form.get('lang', request.args.get('lang', 'th'))  # กำหนดภาษาจากฟอร์มหรือพารามิเตอร์ใน URL (ค่าเริ่มต้นเป็น 'th')

    if request.method == 'POST':  # ถ้าเป็นการค้นหาผ่านฟอร์ม (POST)
        query = request.form['query'].lower()  # รับคำค้นหาจากผู้ใช้และแปลงเป็นตัวพิมพ์เล็กเพื่อการค้นหา

        # ค้นหาจังหวัดจาก ontology (ข้อมูล RDF)
        for s, p, o in g:  # วนลูปผ่านแต่ละ triple (subject, predicate, object) ใน graph
            if isinstance(s, URIRef) and ns.ThaiProvince in g.objects(s, None):  # เช็คว่า subject เป็น URIRef และเป็นจังหวัดไทย
                # หากพบจังหวัดที่ตรงกับคำค้น
                if query in str(s).lower() or query in str(o).lower():  # ตรวจสอบว่า query ตรงกับ subject หรือ object หรือไม่
                    # ตรวจสอบชื่อจังหวัดจาก hasNameOfProvince
                    for pred, obj in g.predicate_objects(s):  # วนลูปผ่าน predicate และ object ของ subject นี้
                        if pred == ns.hasNameOfProvince and isinstance(obj, Literal):  # หาก predicate คือ hasNameOfProvince
                            if obj.language == lang or not obj.language:  # ตรวจสอบภาษาของ obj ถ้าตรงกับภาษาหรือไม่กำหนดภาษา
                                province_name = obj  # เก็บชื่อจังหวัด
                    # เพิ่มข้อมูลของจังหวัดที่พบ
                    for pred, obj in g.predicate_objects(s):  # วนลูปผ่าน predicate และ object ของ subject นี้
                        # ตรวจสอบว่า predicate เป็นค่าที่เกี่ยวข้องกับจังหวัด
                        if pred != ns.type and pred != URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"):  # ไม่ใช้ type
                            # แปลคำ predicate เป็นภาษาไทยหรือภาษาอังกฤษ
                            pred_name = pred.split('#')[-1]  # แยกชื่อ predicate
                            if pred_name in predicate_translations:  # ตรวจสอบว่ามีการแปลใน predicate_translations หรือไม่
                                translated_pred = predicate_translations[pred_name].get(lang, pred_name)  # แปลคำให้เป็นภาษา
                            else:
                                translated_pred = pred_name  # หากไม่มีการแปล ให้ใช้ชื่อ predicate เดิม
                            
                            # ตรวจสอบ obj ว่ามี xml:lang หรือ rdf:datatype
                            if isinstance(obj, Literal):  # หาก obj เป็น Literal (ข้อความ)
                                # หาก obj เป็น Literal เราจะตรวจสอบว่าเป็นภาษาใด
                                if obj.language == lang or not obj.language:  # ตรวจสอบภาษา
                                    # เพิ่มค่าลงใน set เพื่อไม่ให้ซ้ำ
                                    results.add(f"{translated_pred} : {obj}")
                            else:
                                # หาก obj ไม่ใช่ Literal แสดงค่าปกติ
                                results.add(f"{translated_pred} : {str(obj)}")
        
        # ถ้าไม่พบผลลัพธ์
        if not results:
            results.add("ไม่พบข้อมูลที่ค้นหา" if lang == 'th' else "No data found")  # เพิ่มข้อความเมื่อไม่พบข้อมูล

    return render_template('index.html', results=sorted(results), province_name=province_name, lang=lang, current_lang=lang)  # แสดงผลลัพธ์ใน HTML

if __name__ == '__main__':  # ตรวจสอบว่าไฟล์นี้ถูกรันโดยตรง
    app.run(debug=False)  # รันแอปพลิเคชัน Flask โดยไม่เปิดโหมด debug
