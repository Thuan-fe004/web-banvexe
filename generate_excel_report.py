# generate_excel_report.py
import pytest
import sys
import os
import pandas as pd
from datetime import datetime

def run_and_export_excel():
    print("Bắt đầu chạy toàn bộ test trong dự án của bạn...")
    
    # Chạy pytest và xuất XML + HTML
    pytest.main([
        "tests/test_cases/",
        "--junitxml=reports/result.xml",
        "--html=reports/report.html",
        "--self-contained-html",
        "-v",
        "--tb=short"
    ])

    # Tạo thư mục reports nếu chưa có
    os.makedirs("reports", exist_ok=True)

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse("reports/result.xml")
        root = tree.getroot()

        data = []
        for testsuite in root.findall("testsuite"):
            for testcase in testsuite.findall("testcase"):
                name = testcase.get("name")
                classname = testcase.get("classname", "").split(".")[-1]
                time = float(testcase.get("time", 0))

                failure = testcase.find("failure")
                skipped = testcase.find("skipped")

                if failure is not None:
                    status = "FAILED"
                    message = failure.get("message", "")[:150]
                elif skipped is not None:
                    status = "SKIPPED"
                    message = "Test bị bỏ qua"
                else:
                    status = "PASSED"
                    message = "Thành công"

                data.append({
                    "STT": len(data) + 1,
                    "Test ID": f"{classname}.{name}",
                    "Mô tả": name.replace("test_", "").replace("_", " ").title(),
                    "Trạng thái": status,
                    "Thời gian (giây)": round(time, 3),
                    "Ghi chú": message
                })

        # Tạo file Excel đẹp
        df = pd.DataFrame(data)
        total = len(data)
        passed = len(df[df["Trạng thái"] == "PASSED"])
        rate = round(passed/total*100, 2) if total > 0 else 0

        summary = pd.DataFrame([{
            "STT": "TỔNG KẾT",
            "Test ID": f"{passed}/{total}",
            "Mô tả": "TỶ LỆ THÀNH CÔNG",
            "Trạng thái": f"{rate}%",
            "Thời gian (giây)": df["Thời gian (giây)"].sum().round(2),
            "Ghi chú": datetime.now().strftime("%d/%m/%Y %H:%M")
        }])

        output_file = "reports/BaoCao_KetQua_Test_Automation.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            summary.to_excel(writer, sheet_name="Tổng quan", index=False)
            df.to_excel(writer, sheet_name="Chi tiết Test Case", index=False)

        print("\n" + "="*60)
        print("XUẤT BÁO CÁO EXCEL THÀNH CÔNG 100%!")
        print(f"File: {os.path.abspath(output_file)}")
        print(f"Kết quả: {passed}/{total} PASSED ({rate}%)")
        print("="*60)

    except Exception as e:
        print(f"Lỗi: {e}")
        print("Vẫn tạo được báo cáo HTML tại: reports/report.html")

if __name__ == "__main__":
    run_and_export_excel()