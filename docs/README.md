# FaceTrack Project Documentation

## BCA-III Application Level Project

**Project:** Face Recognition Based Attendance System  
**Academic Year:** 2025-26

---

## 📁 Documentation Files

### Front Matter
- `00_TITLE_PAGE.md` - Title page with student and college details
- `01_CERTIFICATE.md` - Certificate from guide and HOD
- `02_DECLARATION.md` - Student declaration
- `03_ACKNOWLEDGEMENT.md` - Acknowledgements
- `04_INDEX.md` - Table of contents with page numbers

### Main Chapters
- `CHAPTER_01.md` - **Introduction**
  - 1.1 Existing System
  - 1.2 Scope of Work
  - 1.3 Operating Environment – Hardware and Software
  - 1.4 Detail Description of Technology Used

- `CHAPTER_02.md` - **Proposed System**
  - 2.1 Proposed System
  - 2.2 Objectives of System
  - 2.3 User Requirements

- `CHAPTER_03.md` - **Analysis and Design**
  - 3.1 Data Flow Diagram (DFD)
  - 3.2 Entity Relationship Diagram (ERD)
  - 3.3 Data Dictionary
  - 3.4 Table Design
  - 3.5 Code Design
  - 3.6 Menu Tree
  - 3.7 Input Screens
  - 3.8 Report Formats
  - 3.9 Test Procedures and Implementation

- `CHAPTER_04.md` - **User Manual**
  - 4.1 User Manual (Admin, Employee, Kiosk)
  - 4.2 Operations Manual / Menu Explanation
  - 4.3 Forms and Report Specifications
  - 4.4 Drawbacks and Limitations
  - 4.5 Proposed Enhancements

- `CHAPTER_05.md` - **Conclusions**

- `CHAPTER_06_BIBLIOGRAPHY.md` - **Bibliography**

### Annexures
- `ANNEXURE_1.md` - **INPUT FORMS WITH DATA** (8 forms with sample data)
- `ANNEXURE_2.md` - **OUTPUT REPORTS WITH DATA** (6 reports with sample data)
- `ANNEXURE_3.md` - **SAMPLE CODE** (6 code samples)

---

## ✏️ TODO: Fill Placeholders

Search and replace these placeholders throughout all files:

| Placeholder | Replace With |
|-------------|-------------|
| `[STUDENT 1 NAME]` | Your first name |
| `[STUDENT 2 NAME]` | Your second name |
| `[ROLL NUMBER/PRN]` | Your roll/PRN numbers |
| `[COLLEGE NAME]` | Your college full name |
| `[GUIDE NAME]` | Your project guide name |
| `[DESIGNATION]` | Guide designation |
| `[HOD NAME]` | HOD name |
| `[DATE]` | Appropriate dates |
| `*[INSERT SCREENSHOT: ...]*` | Insert actual screenshots |

---

## 📸 Screenshots Needed

Take screenshots of your running application for:

**Chapter 4 - User Manual:**
1. Login page
2. Admin dashboard
3. Add employee form
4. Employee list page
5. Face enrollment page with camera
6. Captured face images (3 angles)
7. Kiosk mode - ready screen
8. Kiosk mode - face detected
9. Kiosk mode - successful recognition
10. Kiosk mode - face not recognized
11. Today's attendance page
12. Attendance history page
13. Apply leave form
14. Leave approval dialog
15. Daily report generation page
16. Sample daily attendance report
17. Sample monthly attendance report
18. Employee-wise detailed report
19. System settings page

**Annexure 1:**
20. All input forms (8 forms)

**Annexure 2:**
21. All output reports (6 reports)

---

## 🖨️ Printing Guidelines

### Page Order:
1. 2 blank pages
2. Title Page (Roman: i)
3. Certificate (ii)
4. Declaration (iii)
5. Acknowledgement (iv)
6. Index (v)
7. Chapter 1 - Introduction (Arabic: 2)
8. Chapter 2 - Proposed System (13)
9. Chapter 3 - Analysis and Design (26)
10. Chapter 4 - User Manual (69)
11. Chapter 5 - Conclusions (82)
12. Chapter 6 - Bibliography (88)
13. Annexure 1 - Input Forms (93)
14. Annexure 2 - Output Reports (100)
15. Annexure 3 - Sample Code (103)
16. 2 blank pages

### Formatting:
- **Font:** Times New Roman, 12pt
- **Line Spacing:** 1.5
- **Margins:** 1 inch all sides (Left: 1.5 inch for binding)
- **Page Numbering:** Roman for front matter (i, ii, iii...), Arabic for main content (1, 2, 3...)
- **Headings:** Bold, larger font
- **Code:** Courier New, 10pt

### Binding:
- **Type:** Spiral or Hard binding
- **Color:** Black cover
- **Print:** 2 copies (for college)

---

## 📋 Submission Checklist

- [ ] All placeholders filled with actual information
- [ ] All screenshots inserted
- [ ] Dates updated throughout
- [ ] Student names consistent everywhere
- [ ] DFD and ERD diagrams inserted in Chapter 3
- [ ] Code samples match actual implementation
- [ ] Page numbers adjusted in INDEX
- [ ] Spelling and grammar checked
- [ ] PDF created from all markdown files
- [ ] Page numbering: Roman (i-v) then Arabic (1-110+)
- [ ] 2 printed copies prepared
- [ ] Soft copy CD/DVD prepared (if required)

---

## 🔄 Converting to PDF

**Option 1: Using Pandoc (Recommended)**
```bash
pandoc CHAPTER_01.md -o CHAPTER_01.pdf --pdf-engine=xelatex
```

**Option 2: Using VS Code Extension**
- Install "Markdown PDF" extension
- Open each .md file
- Right-click → "Markdown PDF: Export (pdf)"

**Option 3: Online Converter**
- Visit: markdown-to-pdf.com
- Upload .md files
- Download PDFs

**Option 4: Combine into Single PDF**
```bash
pandoc 00_TITLE_PAGE.md 01_CERTIFICATE.md 02_DECLARATION.md 03_ACKNOWLEDGEMENT.md 04_INDEX.md CHAPTER_01.md CHAPTER_02.md CHAPTER_03.md CHAPTER_04.md CHAPTER_05.md CHAPTER_06_BIBLIOGRAPHY.md ANNEXURE_1.md ANNEXURE_2.md ANNEXURE_3.md -o FaceTrack_Complete_Documentation.pdf --pdf-engine=xelatex --toc
```

---

## 📝 Quick Tips

1. **Consistency:** Use same terminology throughout (e.g., "check-in" not "checkin" or "check in")
2. **Professional Language:** Formal, technical writing
3. **Accuracy:** All technical details must be correct
4. **Completeness:** No section should be blank or incomplete
5. **Screenshots:** Clear, high-resolution, properly cropped
6. **Tables:** Well-formatted with borders
7. **Code:** Properly indented and syntax-highlighted

---

## 📞 Need Help?

**Project Team:**
- [STUDENT 1 NAME]
- [STUDENT 2 NAME]

**Guide:**
- [GUIDE NAME], [DESIGNATION]

---

**Last Updated:** 05 February 2026

**Status:** ✅ Documentation Structure Complete - Ready for Customization

---
