"""
One-off script to build pediatric_surveillance_report.pdf from code + terminal output.
Run from project root: python 06_agents/make_pediatric_surveillance_pdf.py
Requires: pip install reportlab
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, PageBreak

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CODE_FILE = SCRIPT_DIR / "pediatric_surveillance_agents.py"
OUTPUT_PDF = SCRIPT_DIR / "pediatric_surveillance_report.pdf"

# Terminal output (lines 10-214 from terminals/4.txt) - paste of the three agent outputs
TERMINAL_OUTPUT = """
============================================================
AGENT 1 — DATA CONTEXT AGENT
============================================================
Okay, here's a contextual summary of the provided dataset, as Agent 1 – Data Context Agent:

**DATASET OVERVIEW**

This dataset contains injury data spanning from 1999 to 2016. It records the number of total deaths attributed to various injury mechanisms. The dataset includes 198 records, representing a period of approximately 18 years.  The data focuses on a broad categorization of injury mechanisms, offering a snapshot of fatal injuries during this timeframe.

**VARIABLES IDENTIFIED**

The dataset includes the following variables:

*   **year:**  An integer representing the year in which the injury occurred.
*   **injury_mechanism:** A string variable categorizing the type of injury that resulted in death. The available mechanisms cover a range of causes, including "All Mechanisms," "Suffocation," "Firearm," "Poisoning," and various other specific mechanisms.
*   **total_deaths:** An integer representing the number of deaths associated with the corresponding injury mechanism and year.

**DATA QUALITY ISSUES**

*   **No Missing Values:**  Crucially, there are no missing values for any of the variables. This represents a high level of data completeness.
*   **Limited Granularity:** The dataset lacks granular information such as geographic location (e.g., region, state), sex, or age group. This limits the scope of potential analyses and comparisons.

**RECOMMENDED VARIABLES FOR ANALYSIS**

Given the dataset's structure and limited variables, the following variables would be most suitable for initial analysis:

1.  **year:**  Analyzing trends in total deaths over time is a primary focus. Time series analysis could reveal patterns, spikes, or declines in fatalities associated with specific mechanisms.

2.  **injury_mechanism:** Examining the distribution of deaths across different injury mechanisms is essential. Identifying the most frequent mechanisms driving fatalities allows for targeted intervention strategies. Further investigation into the specific mechanisms within categories like "All Mechanisms" could reveal key contributing factors.

3.  **total_deaths:** This variable is the central metric and will be essential for calculating rates (e.g., deaths per year or per mechanism).

============================================================
AGENT 2 — PUBLIC HEALTH SENTINEL AGENT
============================================================
## Public Health Sentinel Agent – Injury Data Report (1999-2016)

**Date:** October 26, 2023
**Agent:** Agent 2 – Public Health Sentinel Agent

**I. KEY METRICS**

*   **Total Deaths (All Mechanisms):**  The overall number of deaths across all years is 20,684. This represents a significant burden of injury-related fatalities.
*   **Highest Recorded Deaths:** 2016 recorded the highest number of deaths (3,432).
*   **Lowest Recorded Deaths:** 1999 recorded the lowest number of deaths (1,908).
*   **Dominant Mechanism:** "All Mechanisms" accounts for the vast majority of deaths (20,684).
*   **Leading Individual Mechanisms:** Suffocation (12,564) and Firearm (6,782) are the most frequent injury mechanisms contributing to mortality.

**II. TEMPORAL TRENDS**

*   **Overall Increasing Trend:** A clear upward trend in total deaths from 1999 to 2016 is evident. While there are fluctuations, the overall direction is one of increasing mortality rates.
*   **Significant Spike (2013-2016):**  A notable increase in deaths occurred between 2013 and 2016.  2013 (3,060 deaths) marked a significant peak, followed by continued increases in the subsequent three years.  Further investigation is required to understand the factors driving this increase.
*   **Decline in Early Years:** The period from 2006 to 2012 shows a decline in total deaths, though this trend is superseded by the 2013-2016 spike.

**III. GEOGRAPHIC CLUSTERS**

No geographic data in this dataset. Analysis is limited to temporal trends and mechanism distribution.

**IV. HIGH-RISK GROUPS**

Due to the lack of demographic data (age, sex, location), specific high-risk groups cannot be identified. However, given the high death tolls associated with "All Mechanisms", "Suffocation", and "Firearm" mechanisms, these categories should be prioritized for further investigation within any future data sets containing this information.

**V. SENTINEL WARNINGS**

*   **Urgent Signal: Increasing Mortality Trend:** The consistently rising trend in total deaths from 1999 to 2016, particularly the dramatic increase from 2013 to 2016, demands immediate attention. The potential causes for this surge need to be thoroughly investigated.
*   **Specific Mechanism Concerns:** The prominence of "Suffocation" and "Firearm" as leading causes of death warrants specific scrutiny. Understanding the factors contributing to fatalities involving these mechanisms is crucial.
*   **Need for Further Investigation:** The lack of granular data significantly limits our ability to pinpoint specific risk factors or vulnerable populations. Collection of additional data (age, location, socioeconomic factors) is strongly recommended.

**Recommendations:**

*   **Detailed Investigation of 2013-2016 Spike:** Conduct a deeper analysis to identify the specific factors driving the mortality increase during this period. This should include a review of relevant policies, changes in demographics, and any other potential contributing factors.
*   **Mechanism-Specific Research:** Further research into the causes of deaths associated with "Suffocation" and "Firearm" mechanisms is essential.
*   **Data Expansion:** Prioritize the collection of additional data elements (age, location, socioeconomic factors) to enable more targeted analysis and identification of high-risk groups.

---

**End of Report – Agent 2**

============================================================
AGENT 3 — PUBLIC HEALTH POLICY ADVISOR
============================================================
## Public Health Policy Report: Injury Data Analysis (1999-2016)

**Prepared by:** Agent 3 – Public Health Policy Advisor
**Date:** October 26, 2023

**I. SUMMARY OF FINDINGS**

This analysis of injury data from 1999 to 2016 reveals a concerning and persistent trend: a significant increase in total deaths attributed to injury mechanisms over the 18-year period.  The dataset demonstrates a clear upward trajectory, punctuated by a dramatic spike in mortality between 2013 and 2016. While "All Mechanisms" accounts for the vast majority of deaths, "Suffocation" and "Firearm" mechanisms consistently rank as the leading causes of fatalities. The absence of granular demographic data – specifically location, age, and sex – severely limits the ability to identify specific risk groups or localized hotspots, though the dominant mechanisms highlight areas of concern requiring immediate attention.

**II. AREAS OF CONCERN**

*   **Persistent Increase in Mortality:** The overarching trend of rising fatalities across the entire period is the most significant concern. This suggests a systemic issue demanding immediate investigation and intervention.
*   **2013-2016 Spike:** The sharp increase in deaths from 2013 to 2016 represents a critical anomaly that warrants focused scrutiny. Understanding the root causes of this spike is paramount.
*   **"Suffocation" and "Firearm" Dominance:** The consistent prominence of "Suffocation" and "Firearm" mechanisms as major drivers of fatalities demands immediate attention. These mechanisms often indicate underlying societal issues related to mental health, access to resources, and potentially, public safety policies.
*   **Data Limitations:** The lack of granular data significantly hinders our ability to identify specific risk groups and understand the context surrounding these injuries.


**III. LIKELY PUBLIC HEALTH DRIVERS**

Given the data and sentinel analysis, several potential public health drivers likely contribute to the observed trends:

*   **Mental Health Crisis:** The dominance of "Suffocation" suggests a potential link to increasing rates of suicide and mental health challenges.  Factors contributing to this could include reduced access to mental health services, stigma surrounding mental illness, or economic stressors.
*   **Firearm Violence:** The prominent role of "Firearm" injuries highlights the issue of firearm violence, including intentional shootings, accidental deaths, and potential suicides.  Contributing factors might include firearm access, lack of gun safety education, and societal inequalities.
*   **Socioeconomic Factors:** While the dataset lacks direct socioeconomic data, the overall trend could be influenced by broader factors such as poverty, unemployment, and lack of access to healthcare. These factors can exacerbate existing vulnerabilities and contribute to injury risk.
*   **Policy Changes:** The 2013-2016 spike may have been influenced by changes in relevant policies or regulations, requiring a thorough investigation of potential impacts.

**IV. RECOMMENDED INTERVENTIONS**

*   **Investigate the 2013-2016 Spike:** Implement a rapid, targeted investigation into the causes of the significant mortality increase between 2013 and 2016. This should include a review of relevant surveillance data, policy changes, and societal trends.
*   **Expand Mental Health Services:** Increase access to mental health services, particularly suicide prevention programs, addressing issues of stigma and ensuring equitable access to care.
*   **Firearm Safety Initiatives:** Implement comprehensive firearm safety education programs, particularly for young people, and explore strategies to reduce firearm access and promote responsible gun ownership.
*   **Data Collection Expansion:** Immediately prioritize the collection of demographic data (age, sex, location, socioeconomic status) to allow for more targeted analysis and identification of high-risk populations and geographic areas.
*   **Mechanism-Specific Prevention Programs:** Develop and implement targeted prevention programs specifically addressing "Suffocation" and "Firearm" injuries. This might include campaigns focused on safe sleep practices, responsible firearm storage, and suicide prevention messaging.
*   **Community-Based Surveillance:** Establish local injury surveillance systems to track trends in specific mechanisms and identify emerging risks within communities.


**V. PRIORITY ACTIONS FOR POLICYMAKERS**

*   **Secure Funding for Rapid Investigation:** Allocate resources immediately to conduct a thorough investigation of the 2013-2016 mortality spike.
*   **Prioritize Mental Health Funding:** Increase funding for mental health services, including suicide prevention and crisis intervention programs, with a focus on expanding access for vulnerable populations.
*   **Support Firearms Violence Prevention Programs:** Invest in community-based programs focused on reducing firearm violence, encompassing education, access control, and violence prevention strategies.
*   **Advocate for Data Collection Expansion:**  Work with relevant agencies to develop and implement a plan for collecting critical demographic data related to injury incidence and mortality.
*   **Establish a Multi-Disciplinary Task Force:**  Create a task force comprised of public health professionals, law enforcement, healthcare providers, and community representatives to coordinate a comprehensive response to the identified challenges.

---

End of Report – Agent 3
"""


def wrap_lines(text, max_chars=88):
    """Break long lines so they fit on the page and are not cut off."""
    lines = []
    for line in text.splitlines():
        if len(line) <= max_chars:
            lines.append(line)
            continue
        while line:
            if len(line) <= max_chars:
                lines.append(line)
                break
            # Break at last space before max_chars, or at max_chars
            chunk = line[: max_chars + 1]
            last_space = chunk.rfind(" ")
            if last_space > max_chars // 2:
                cut = last_space + 1
            else:
                cut = max_chars
            lines.append(line[:cut].rstrip())
            line = line[cut:].lstrip() if len(line) > cut else ""
    return "\n".join(lines)


def main():
    code_text = CODE_FILE.read_text(encoding="utf-8")
    styles = getSampleStyleSheet()
    code_style = ParagraphStyle(
        name="Code",
        fontName="Courier",
        fontSize=7,
        leading=8,
        leftIndent=0,
        rightIndent=0,
    )
    output_style = ParagraphStyle(
        name="Output",
        fontName="Courier",
        fontSize=8,
        leading=10,
        leftIndent=0,
        rightIndent=0,
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    story = []

    story.append(Paragraph(
        "Multi-Agent Pediatric Suicide Surveillance: Code and Output",
        styles["Title"],
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("1. Code (pediatric_surveillance_agents.py)", styles["Heading1"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Preformatted(wrap_lines(code_text, max_chars=88), code_style))
    story.append(PageBreak())

    story.append(Paragraph("2. Run Output (Three Agents)", styles["Heading1"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Preformatted(wrap_lines(TERMINAL_OUTPUT.strip(), max_chars=88), output_style))

    doc.build(story)
    print("Wrote:", OUTPUT_PDF)


if __name__ == "__main__":
    main()
