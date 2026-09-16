import argparse
import calendar
import datetime
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4
SIDEBAR_WIDTH = 42
CONTENT_WIDTH = PAGE_WIDTH - SIDEBAR_WIDTH - 20
MARGIN = 24

# 配色系統（清爽低飽和度灰階）
C_BORDER = HexColor("#D0D0D0")
C_LINE = HexColor("#EAEAEA")
C_TEXT_DARK = HexColor("#222222")
C_TEXT_MUTED = HexColor("#777777")
C_DOT = HexColor("#C8C8C8")
C_CARD_BG = HexColor("#FBFBFB")

WEEKDAYS_CN = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
MONTH_NAMES_EN = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# 內建繁體中文字型（完全避開外部網路與缺少字型問題）
pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
FONT = "MSung-Light"


class NotesFirstPlanner:

  def __init__(self, filename, year, inc_annual, inc_month, inc_week, inc_day):
    self.filename = filename
    self.year = int(year)
    self.inc_annual = inc_annual
    self.inc_month = inc_month
    self.inc_week = inc_week
    self.inc_day = inc_day

    self.c = canvas.Canvas(self.filename, pagesize=A4)
    self.week_list = []
    self.date_to_iso_week = {}
    self._prepare_iso_weeks()

  def _prepare_iso_weeks(self):
    start_date = datetime.date(self.year, 1, 1)
    end_date = datetime.date(self.year, 12, 31)

    cur = start_date - datetime.timedelta(days=start_date.weekday())
    seen_weeks = set()

    while cur <= end_date or (
        cur.year == self.year and cur.weekday() != 0
    ):
      iso_year, iso_week, _ = cur.isocalendar()
      week_key = (iso_year, iso_week)

      if week_key not in seen_weeks:
        seen_weeks.add(week_key)
        days = [cur + datetime.timedelta(days=i) for i in range(7)]
        self.week_list.append((iso_year, iso_week, days))

      cur += datetime.timedelta(days=7)

    cur_d = start_date
    while cur_d <= end_date:
      y, w, _ = cur_d.isocalendar()
      self.date_to_iso_week[cur_d] = (y, w)
      cur_d += datetime.timedelta(days=1)

  def draw_dot_grid(self, x, y, width, height, spacing=13):
    self.c.setFillColor(C_DOT)
    nx = int(width // spacing)
    ny = int(height // spacing)
    for i in range(1, nx):
      for j in range(1, ny):
        self.c.circle(x + i * spacing, y + j * spacing, 0.55, fill=1, stroke=0)

  def draw_sidebar(self, current_type="home", current_month=None):
    sb_x = PAGE_WIDTH - SIDEBAR_WIDTH
    self.c.setStrokeColor(C_LINE)
    self.c.setLineWidth(0.8)
    self.c.line(sb_x, 0, sb_x, PAGE_HEIGHT)

    # 1. ⌂ 首頁 HOME 按鈕
    y_home = PAGE_HEIGHT - 32
    is_home = current_type == "home"
    self.c.setFillColor(C_TEXT_DARK if is_home else C_TEXT_MUTED)
    self.c.setFont(FONT, 12)
    self.c.drawCentredString(sb_x + SIDEBAR_WIDTH / 2, y_home, "⌂")
    self.c.linkRect(
        "",
        "dest_home",
        (sb_x, y_home - 6, sb_x + SIDEBAR_WIDTH, y_home + 14),
        Border="[0 0 0]",
    )

    # 2. YEAR 按鈕
    y_year = y_home - 28
    is_year = current_type == "annual"
    self.c.setFillColor(C_TEXT_DARK if is_year else C_TEXT_MUTED)
    self.c.setFont(FONT, 8.5)
    self.c.drawCentredString(sb_x + SIDEBAR_WIDTH / 2, y_year, "YEAR")
    if self.inc_annual:
      self.c.linkRect(
          "",
          "dest_annual",
          (sb_x, y_year - 6, sb_x + SIDEBAR_WIDTH, y_year + 14),
          Border="[0 0 0]",
      )

    # 3. 01 ~ 12 月份按鈕（當前月自動加深顯著化）
    slot_h = (PAGE_HEIGHT - 130) / 12
    start_m_y = y_year - 24
    for m in range(1, 13):
      cur_y = start_m_y - (m - 1) * slot_h
      is_cur_m = current_month == m
      self.c.setFillColor(C_TEXT_DARK if is_cur_m else C_TEXT_MUTED)
      self.c.setFont(FONT, 9.5 if is_cur_m else 8.5)
      self.c.drawCentredString(sb_x + SIDEBAR_WIDTH / 2, cur_y, f"{m:02d}")
      if self.inc_month:
        self.c.linkRect(
            "",
            f"dest_m_{m}",
            (sb_x, cur_y - 6, sb_x + SIDEBAR_WIDTH, cur_y + 12),
            Border="[0 0 0]",
        )

  # --------------------------------------------------
  # 0. 🏠 首頁 Index（純傳送門）
  # --------------------------------------------------
  def build_home_page(self):
    self.c.bookmarkPage("dest_home")
    self.draw_sidebar("home")

    self.c.setFont(FONT, 26)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN, PAGE_HEIGHT - 58, f"{self.year} DIGITAL PLANNER")
    self.c.setFont(FONT, 10)
    self.c.setFillColor(C_TEXT_MUTED)
    self.c.drawString(
        MARGIN, PAGE_HEIGHT - 76, "筆記手帳快速索引 ． 點擊方塊跳轉"
    )

    btn_w = CONTENT_WIDTH - MARGIN
    self.c.setStrokeColor(C_BORDER)
    self.c.setFillColor(C_CARD_BG)
    self.c.rect(MARGIN, PAGE_HEIGHT - 130, btn_w, 38, fill=1, stroke=1)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.setFont(FONT, 12)
    self.c.drawCentredString(
        MARGIN + btn_w / 2, PAGE_HEIGHT - 114, "年度總覽計畫 (YEAR OVERVIEW)"
    )
    if self.inc_annual:
      self.c.linkRect(
          "",
          "dest_annual",
          (MARGIN, PAGE_HEIGHT - 130, MARGIN + btn_w, PAGE_HEIGHT - 92),
          Border="[0 0 0]",
      )

    cols, rows = 3, 4
    grid_y = PAGE_HEIGHT - 150
    grid_h = grid_y - (MARGIN + 20)
    cw = (btn_w - 20) / cols
    rh = (grid_h - 25) / rows

    for m in range(1, 13):
      r = (m - 1) // cols
      c = (m - 1) % cols
      x = MARGIN + c * (cw + 10)
      y = grid_y - (r + 1) * rh

      self.c.setStrokeColor(C_LINE)
      self.c.setFillColor(C_CARD_BG)
      self.c.rect(x, y, cw, rh - 8, fill=1, stroke=1)

      self.c.setFillColor(C_TEXT_DARK)
      self.c.setFont(FONT, 14)
      self.c.drawString(x + 14, y + rh - 30, f"{m:02d}")
      self.c.setFont(FONT, 9.5)
      self.c.setFillColor(C_TEXT_MUTED)
      self.c.drawString(x + 40, y + rh - 29, MONTH_NAMES_EN[m - 1])

      if self.inc_month:
        self.c.linkRect(
            "", f"dest_m_{m}", (x, y, x + cw, y + rh - 8), Border="[0 0 0]"
        )

    self.c.showPage()

  # --------------------------------------------------
  # 1. 📅 年度計畫（年度大目標＋大事紀）
  # --------------------------------------------------
  def build_annual_page(self):
    self.c.bookmarkPage("dest_annual")
    self.draw_sidebar("annual")

    self.c.setFont(FONT, 20)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN, PAGE_HEIGHT - 45, f"{self.year} 年度目標與展望")

    self.c.setFont(FONT, 9)
    self.c.setFillColor(C_TEXT_MUTED)
    self.c.drawRightString(CONTENT_WIDTH, PAGE_HEIGHT - 42, "⌂ HOME")
    self.c.linkRect(
        "",
        "dest_home",
        (CONTENT_WIDTH - 50, PAGE_HEIGHT - 48, CONTENT_WIDTH, PAGE_HEIGHT - 32),
        Border="[0 0 0]",
    )

    gw = CONTENT_WIDTH - MARGIN

    top_y = PAGE_HEIGHT - 75
    top_h = 160
    self.c.setStrokeColor(C_BORDER)
    self.c.rect(MARGIN, top_y - top_h, gw, top_h, fill=0, stroke=1)
    self.c.setFont(FONT, 10.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN + 12, top_y - 20, "年度核心目標與專案 (ANNUAL PRIORITIES)"
    )

    for i in range(5):
      gy = top_y - 45 - i * 24
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(MARGIN + 15, gy, 8, 8, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN + 32, gy, MARGIN + gw - 15, gy)

    bottom_top = top_y - top_h - 20
    bottom_h = bottom_top - MARGIN
    slot_h = bottom_h / 12

    for m in range(1, 13):
      sy = bottom_top - (m) * slot_h
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN, sy, MARGIN + gw, sy)

      self.c.setFont(FONT, 9)
      self.c.setFillColor(C_TEXT_DARK)
      self.c.drawString(MARGIN + 5, sy + slot_h - 13, f"{m:02d}月")
      if self.inc_month:
        self.c.linkRect(
            "",
            f"dest_m_{m}",
            (MARGIN, sy, MARGIN + 35, sy + slot_h),
            Border="[0 0 0]",
        )

      self.draw_dot_grid(
          MARGIN + 45, sy + 2, gw - 50, slot_h - 4, spacing=11
      )

    self.c.showPage()

  # --------------------------------------------------
  # 2. 🗓 月計畫（乾淨大月曆＋下方本月待辦）
  # --------------------------------------------------
  def build_month_page(self, month):
    self.c.bookmarkPage(f"dest_m_{month}")
    self.draw_sidebar("month", current_month=month)

    self.c.setFont(FONT, 20)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN,
        PAGE_HEIGHT - 45,
        f"{self.year} / {month:02d}月  {MONTH_NAMES_EN[month-1]}",
    )

    self.c.setFont(FONT, 8.5)
    self.c.setFillColor(C_TEXT_MUTED)
    self.c.drawRightString(
        CONTENT_WIDTH, PAGE_HEIGHT - 42, "← YEAR   |   ⌂ HOME"
    )
    if self.inc_annual:
      self.c.linkRect(
          "",
          "dest_annual",
          (CONTENT_WIDTH - 110, PAGE_HEIGHT - 48, CONTENT_WIDTH - 60, PAGE_HEIGHT - 32),
          Border="[0 0 0]",
      )
    self.c.linkRect(
        "",
        "dest_home",
        (CONTENT_WIDTH - 55, PAGE_HEIGHT - 48, CONTENT_WIDTH, PAGE_HEIGHT - 32),
        Border="[0 0 0]",
    )

    cal = calendar.monthcalendar(self.year, month)
    cal_top = PAGE_HEIGHT - 75
    cal_h = (PAGE_HEIGHT - 130) * 0.66
    gw = CONTENT_WIDTH - MARGIN
    col_w = gw / 7
    row_h = (cal_h - 18) / len(cal)

    self.c.setFont(FONT, 8.5)
    self.c.setFillColor(C_TEXT_MUTED)
    for i, w in enumerate(WEEKDAYS_CN):
      self.c.drawString(MARGIN + i * col_w + 6, cal_top - 12, w)

    self.c.setStrokeColor(C_LINE)
    self.c.line(MARGIN, cal_top - 16, MARGIN + gw, cal_top - 16)

    for r_idx, week in enumerate(cal):
      cur_y = cal_top - 16 - (r_idx + 1) * row_h
      for c_idx, day in enumerate(week):
        cur_x = MARGIN + c_idx * col_w
        self.c.setStrokeColor(C_LINE)
        self.c.rect(cur_x, cur_y, col_w, row_h, fill=0, stroke=1)
        if day != 0:
          self.c.setFont(FONT, 9)
          self.c.setFillColor(C_TEXT_DARK)
          self.c.drawString(cur_x + 6, cur_y + row_h - 14, str(day))
          if self.inc_day:
            self.c.linkRect(
                "",
                f"dest_d_{month}_{day}",
                (cur_x + 3, cur_y + row_h - 16, cur_x + 24, cur_y + row_h),
                Border="[0 0 0]",
            )

    bottom_y = MARGIN + 10
    bottom_h = (PAGE_HEIGHT - 130) * 0.30
    half_w = (gw - 15) / 2

    self.c.setStrokeColor(C_BORDER)
    self.c.rect(MARGIN, bottom_y, half_w, bottom_h, fill=0, stroke=1)
    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN + 10, bottom_y + bottom_h - 16, "本月重大待辦 (TASKS)")
    for i in range(5):
      gy = bottom_y + bottom_h - 34 - i * 18
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(MARGIN + 12, gy, 7, 7, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN + 25, gy, MARGIN + half_w - 10, gy)

    rx = MARGIN + half_w + 15
    self.c.setStrokeColor(C_BORDER)
    self.c.rect(rx, bottom_y, half_w, bottom_h, fill=0, stroke=1)
    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(rx + 10, bottom_y + bottom_h - 16, "自由備忘 (NOTES)")
    self.draw_dot_grid(
        rx + 5, bottom_y + 4, half_w - 10, bottom_h - 26, spacing=10
    )

    self.c.showPage()

  # --------------------------------------------------
  # 3. 📖 週計畫（左 7 天日程備忘＋右大面積待辦筆記）
  # --------------------------------------------------
  def build_week_page(self, iso_year, week_num, days_in_week):
    self.c.bookmarkPage(f"dest_w_{iso_year}_{week_num}")
    mid_month = days_in_week[3].month
    self.draw_sidebar("week", current_month=mid_month)

    first_d = days_in_week[0].strftime("%m.%d")
    last_d = days_in_week[-1].strftime("%m.%d")

    self.c.setFont(FONT, 18)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN,
        PAGE_HEIGHT - 45,
        f"WEEK {week_num:02d}   ({first_d} - {last_d})",
    )

    self.c.setFont(FONT, 8.5)
    self.c.setFillColor(C_TEXT_MUTED)
    self.c.drawRightString(
        CONTENT_WIDTH, PAGE_HEIGHT - 42, f"← {mid_month:02d}月   |   ⌂ HOME"
    )
    if self.inc_month:
      self.c.linkRect(
          "",
          f"dest_m_{mid_month}",
          (CONTENT_WIDTH - 100, PAGE_HEIGHT - 48, CONTENT_WIDTH - 55, PAGE_HEIGHT - 32),
          Border="[0 0 0]",
      )
    self.c.linkRect(
        "",
        "dest_home",
        (CONTENT_WIDTH - 50, PAGE_HEIGHT - 48, CONTENT_WIDTH, PAGE_HEIGHT - 32),
        Border="[0 0 0]",
    )

    body_y = MARGIN + 10
    body_h = PAGE_HEIGHT - 85
    left_w = (CONTENT_WIDTH - MARGIN) * 0.44
    right_w = (CONTENT_WIDTH - MARGIN) * 0.56

    day_slot_h = body_h / 7
    for idx, d in enumerate(days_in_week):
      slot_y = (body_y + body_h) - (idx + 1) * day_slot_h
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN, slot_y, MARGIN + left_w, slot_y)

      self.c.setFont(FONT, 9.5)
      self.c.setFillColor(C_TEXT_DARK)
      day_title = f"{d.month:02d}.{d.day:02d}  {WEEKDAYS_CN[d.weekday()]}"
      self.c.drawString(MARGIN + 6, slot_y + day_slot_h - 15, day_title)

      if self.inc_day and d.year == self.year:
        self.c.linkRect(
            "",
            f"dest_d_{d.month}_{d.day}",
            (MARGIN, slot_y + day_slot_h - 20, MARGIN + 85, slot_y + day_slot_h),
            Border="[0 0 0]",
        )

      self.draw_dot_grid(
          MARGIN + 90, slot_y + 2, left_w - 92, day_slot_h - 6, spacing=10
      )

    self.c.setStrokeColor(C_BORDER)
    self.c.line(MARGIN + left_w, body_y, MARGIN + left_w, body_y + body_h)

    rx = MARGIN + left_w + 14
    rw = right_w - 14

    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(rx, body_y + body_h - 12, "本週待辦清單 (WEEKLY TO-DO)")
    for i in range(6):
      gy = (body_y + body_h - 30) - i * 19
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(rx, gy, 8, 8, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(rx + 16, gy, rx + rw - 5, gy)

    ny = body_y + body_h - 160
    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(rx, ny, "靈感與筆記 (BRAIN DUMP & NOTES)")
    self.draw_dot_grid(rx, body_y + 2, rw - 5, ny - body_y - 8, spacing=11)

    self.c.showPage()

  # --------------------------------------------------
  # 4. 📝 日計畫（筆記優先版：極簡頂部＋65% 大留白點陣）
  # --------------------------------------------------
  def build_day_page(self, cur_date):
    m, d = cur_date.month, cur_date.day
    iso_year, iso_w = self.date_to_iso_week.get(
        cur_date, cur_date.isocalendar()[:2]
    )

    self.c.bookmarkPage(f"dest_d_{m}_{d}")
    self.draw_sidebar("day", current_month=m)

    self.c.setFont(FONT, 20)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN, PAGE_HEIGHT - 45, f"{m:02d}月{d:02d}日 {WEEKDAYS_CN[cur_date.weekday()]}"
    )

    self.c.setFont(FONT, 8.5)
    self.c.setFillColor(C_TEXT_MUTED)
    self.c.drawRightString(
        CONTENT_WIDTH,
        PAGE_HEIGHT - 42,
        f"← WEEK {iso_w:02d}   |   ← {m:02d}月   |   ⌂ HOME",
    )

    if self.inc_week:
      self.c.linkRect(
          "",
          f"dest_w_{iso_year}_{iso_w}",
          (CONTENT_WIDTH - 165, PAGE_HEIGHT - 48, CONTENT_WIDTH - 105, PAGE_HEIGHT - 32),
          Border="[0 0 0]",
      )
    if self.inc_month:
      self.c.linkRect(
          "",
          f"dest_m_{m}",
          (CONTENT_WIDTH - 100, PAGE_HEIGHT - 48, CONTENT_WIDTH - 55, PAGE_HEIGHT - 32),
          Border="[0 0 0]",
      )
    self.c.linkRect(
        "",
        "dest_home",
        (CONTENT_WIDTH - 50, PAGE_HEIGHT - 48, CONTENT_WIDTH, PAGE_HEIGHT - 32),
        Border="[0 0 0]",
    )

    gw = CONTENT_WIDTH - MARGIN

    top_block_y = PAGE_HEIGHT - 70
    top_block_h = 135
    half_w = (gw - 15) / 2

    # 左：今日 3 大優先焦點
    self.c.setStrokeColor(C_BORDER)
    self.c.rect(MARGIN, top_block_y - top_block_h, half_w, top_block_h, fill=0, stroke=1)
    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN + 10, top_block_y - 18, "今日 3 大核心焦點 (TOP 3 PRIORITIES)")
    for i in range(3):
      fy = top_block_y - 45 - i * 32
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(MARGIN + 12, fy, 8, 8, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN + 26, fy, MARGIN + half_w - 12, fy)

    # 右：今日待辦
    rx = MARGIN + half_w + 15
    self.c.setStrokeColor(C_BORDER)
    self.c.rect(rx, top_block_y - top_block_h, half_w, top_block_h, fill=0, stroke=1)
    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(rx + 10, top_block_y - 18, "待辦清單 (TO-DO LIST)")
    for i in range(5):
      ty = top_block_y - 42 - i * 19
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(rx + 12, ty, 7, 7, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(rx + 25, ty, rx + half_w - 12, ty)

    # 下半部大留白筆記區
    notes_top = top_block_y - top_block_h - 18
    notes_bottom = MARGIN + 10
    notes_h = notes_top - notes_bottom

    self.c.setFont(FONT, 9.5)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN, notes_top, "筆記、記錄與反思 (DAILY NOTES)")

    time_markers = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
    marker_slot = (notes_h - 20) / len(time_markers)

    self.c.setFont(FONT, 8.5)
    self.c.setFillColor(C_TEXT_MUTED)
    for idx, t_str in enumerate(time_markers):
      my = notes_top - 20 - idx * marker_slot
      self.c.drawString(MARGIN + 2, my - 3, t_str)
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN + 34, my, MARGIN + 42, my)

    self.draw_dot_grid(
        MARGIN + 48, notes_bottom, gw - 48, notes_h - 18, spacing=12
    )

    self.c.showPage()

  # --------------------------------------------------
  # 主執行
  # --------------------------------------------------
  def generate(self):
    self.build_home_page()

    if self.inc_annual:
      self.build_annual_page()

    if self.inc_month:
      for m in range(1, 13):
        self.build_month_page(m)

    if self.inc_week:
      for iso_year, w_num, days in self.week_list:
        self.build_week_page(iso_year, w_num, days)

    if self.inc_day:
      cur = datetime.date(self.year, 1, 1)
      end = datetime.date(self.year, 12, 31)
      one_day = datetime.timedelta(days=1)
      while cur <= end:
        self.build_day_page(cur)
        cur += one_day

    self.c.save()


def str_to_bool(value):
  return str(value).lower() in ("true", "1", "yes", "y")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--year", type=int, default=2026)
  parser.add_argument("--annual", type=str_to_bool, default=True)
  parser.add_argument("--month", type=str_to_bool, default=True)
  parser.add_argument("--week", type=str_to_bool, default=True)
  parser.add_argument("--day", type=str_to_bool, default=True)
  parser.add_argument("--output", type=str, default="planner.pdf")
  args = parser.parse_args()

  planner = NotesFirstPlanner(
      args.output, args.year, args.annual, args.month, args.week, args.day
  )
  planner.generate()
  print(f"Notes-First 手帳生成完畢：{args.output}")
