from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=14)
pdf.cell(200, 10, txt="A Suficiência de Cristo", ln=True, align='C')
pdf.ln(10)
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt="Cristo é suficiente para a salvação, para a vida e para a eternidade. A teologia cristã histórica afirma que não há outro mediador entre Deus e os homens, senão Jesus Cristo (1Tm 2:5). A suficiência de Cristo é o fundamento da fé reformada e da confiança do cristão.")
pdf.output('j:/Projetos Python/eklesia.ia.python/tests/files/teste.pdf')
