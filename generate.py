import argparse
import calendar
import datetime
import os
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4
SIDEBAR_WIDTH = 45
CONTENT_WIDTH = PAGE_WIDTH - SIDEBAR_WIDTH - 20
MARGIN = 25

C_BORDER = HexColor("#D0D0D0")
C_LINE = HexColor("#E5E5E5")
C_TEXT_DARK = HexColor("#1A1A1A")
C_TEXT_MUTED = HexColor("#737373")
C_DOT = HexColor("#C4C4C4")

WEEKDAYS_CN = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def register_chinese_fonts():
  """尋找並註冊系統中的中文字型"""
  font_candidates = [
      # Ubuntu / GitHub Actions (fonts-noto-cjk)
      (
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
      ),
      (
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
      ),
      # Windows
      ("C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjhbd.ttc"),
      # macOS
      ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/PingFang.ttc"),
  ]

  regular_font = None
  bold_font = None

  for reg_path, bold_path in font_candidates:
    if os.path.exists(reg_path):
      regular_font = reg_path
      bold_font = bold_path if os.path.exists(bold_path) else reg_path
      break

  if regular_font:
    pdfmetrics.registerFont(TTFont("ChineseRegular", regular_font))
    pdfmetrics.registerFont(TTFont("ChineseBold", bold_font))
    return "ChineseRegular", "ChineseBold"
  else:
    return "Helvetica", "Helvetica-Bold"


FONT_REGULAR, FONT_BOLD = register_chinese_fonts()


class KudrykvStylePlanner:

  def __init__(self, filename, year, inc_annual, inc_month, inc_week, inc_day):
    self.filename = filename
    self.year = int(year)
    self.inc_annual = inc_annual
    self.inc_month = inc_month
    self.inc_week = inc_week
    self.inc_day = inc_day
    self.c = canvas.Canvas(self.filename, pagesize=A4)

  def draw_dot_grid(self, x, y, width, height, spacing=14):
    self.c.setFillColor(C_DOT)
    nx = int(width // spacing)
    ny = int(height // spacing)
    for i in range(1, nx):
      for j in range(1, ny):
        self.c.circle(x + i * spacing, y + j * spacing, 0.6, fill=1, stroke=0)

  def draw_sidebar(self, current_type="annual", current_val=None):
    sb_x = PAGE_WIDTH - SIDEBAR_WIDTH
    self.c.setStrokeColor(C_LINE)
    self.c.setLineWidth(0.8)
    self.c.line(sb_x, 0, sb_x, PAGE_HEIGHT)

    y_top = PAGE_HEIGHT - 40
    if self.inc_annual:
      self.c.setFillColor(
          C_TEXT_DARK if current_type == "annual" else C_TEXT_MUTED
      )
      self.c.setFont(FONT_BOLD, 11)
      self.c.drawCentredString(sb_x + SIDEBAR_WIDTH / 2, y_top, str(self.year))
      self.c.linkRect(
          "",
          "dest_annual",
          (sb_x, y_top - 5, sb_x + SIDEBAR_WIDTH, y_top + 15),
          Border="[0 0 0]",
      )

    if self.inc_month:
      start_m_y = y_top - 40
      slot_h = 32
      for m in range(1, 13):
        cur_y = start_m_y - (m - 1) * slot_h
        is_cur = current_type == "month" and current_val == m
        self.c.setFillColor(C_TEXT_DARK if is_cur else C_TEXT_MUTED)
        self.c.setFont(FONT_BOLD if is_cur else FONT_REGULAR, 9)
        self.c.drawCentredString(sb_x + SIDEBAR_WIDTH / 2, cur_y, f"{m:02d}月")
        self.c.linkRect(
            "",
            f"dest_m_{m}",
            (sb_x, cur_y - 6, sb_x + SIDEBAR_WIDTH, cur_y + 14),
            Border="[0 0 0]",
        )

  def build_annual_page(self):
    self.c.bookmarkPage("dest_annual")
    self.draw_sidebar("annual")
    self.c.setFont(FONT_BOLD, 24)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN, PAGE_HEIGHT - 50, f"{self.year}")

    cols, rows = 3, 4
    cw = (CONTENT_WIDTH - MARGIN) / cols
    rh = (PAGE_HEIGHT - 130) / rows

    for m in range(1, 13):
      r = (m - 1) // cols
      c = (m - 1) % cols
      x = MARGIN + c * cw
      y = (PAGE_HEIGHT - 90) - r * rh

      self.c.setFont(FONT_BOLD, 11)
      self.c.setFillColor(C_TEXT_DARK)
      self.c.drawString(x, y, f"{m:02d}月")
      if self.inc_month:
        self.c.linkRect(
            "", f"dest_m_{m}", (x, y - 2, x + 40, y + 14), Border="[0 0 0]"
        )

      cal = calendar.monthcalendar(self.year, m)
      self.c.setFont(FONT_REGULAR, 6.5)
      self.c.setFillColor(C_TEXT_MUTED)
      col_w = (cw - 15) / 7
      for idx, w_name in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
        self.c.drawCentredString(x + idx * col_w + 5, y - 14, w_name)

      self.c.setFont(FONT_REGULAR, 7)
      for row_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
          if day != 0:
            dy = y - 26 - row_idx * 11
            dx = x + day_idx * col_w + 5
            self.c.setFillColor(C_TEXT_DARK)
            self.c.drawCentredString(dx, dy, str(day))
            if self.inc_day:
              self.c.linkRect(
                  "",
                  f"dest_d_{m}_{day}",
                  (dx - 4, dy - 2, dx + 4, dy + 7),
                  Border="[0 0 0]",
              )
    self.c.showPage()

  def build_month_page(self, month):
    self.c.bookmarkPage(f"dest_m_{month}")
    self.draw_sidebar("month", month)
    self.c.setFont(FONT_BOLD, 20)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(MARGIN, PAGE_HEIGHT - 50, f"{self.year} / {month:02d}月")

    cal = calendar.monthcalendar(self.year, month)
    gx, gy = MARGIN, MARGIN + 20
    gw = CONTENT_WIDTH - MARGIN
    gh = PAGE_HEIGHT - 100
    col_w = gw / 7
    row_h = (gh - 25) / len(cal)

    self.c.setFont(FONT_BOLD, 9)
    self.c.setFillColor(C_TEXT_MUTED)
    for i, w in enumerate(WEEKDAYS_CN):
      self.c.drawString(gx + i * col_w + 5, gy + gh - 15, w)

    self.c.setStrokeColor(C_LINE)
    self.c.setLineWidth(0.6)
    self.c.line(gx, gy + gh - 20, gx + gw, gy + gh - 20)

    for r_idx, week in enumerate(cal):
      cur_y = gy + gh - 20 - (r_idx + 1) * row_h
      for c_idx, day in enumerate(week):
        cur_x = gx + c_idx * col_w
        self.c.setStrokeColor(C_LINE)
        self.c.rect(cur_x, cur_y, col_w, row_h, fill=0, stroke=1)
        if day != 0:
          self.c.setFont(FONT_BOLD, 9)
          self.c.setFillColor(C_TEXT_DARK)
          self.c.drawString(cur_x + 6, cur_y + row_h - 14, str(day))
          if self.inc_day:
            self.c.linkRect(
                "",
                f"dest_d_{month}_{day}",
                (cur_x + 4, cur_y + row_h - 16, cur_x + 25, cur_y + row_h),
                Border="[0 0 0]",
            )
          self.draw_dot_grid(cur_x, cur_y, col_w, row_h - 18, spacing=10)
    self.c.showPage()

  def build_week_page(self, week_num, days_in_week):
    self.c.bookmarkPage(f"dest_w_{week_num}")
    self.draw_sidebar("week", days_in_week[0].month)

    first_d = days_in_week[0].strftime("%m.%d")
    last_d = days_in_week[-1].strftime("%m.%d")
    self.c.setFont(FONT_BOLD, 16)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN,
        PAGE_HEIGHT - 45,
        f"第 {week_num:02d} 週  ({first_d} - {last_d})",
    )

    gw = CONTENT_WIDTH - MARGIN
    slot_h = (PAGE_HEIGHT - 90) / 7

    for idx, d in enumerate(days_in_week):
      slot_y = (PAGE_HEIGHT - 65) - (idx + 1) * slot_h
      self.c.setStrokeColor(C_BORDER)
      self.c.setLineWidth(0.6)
      self.c.line(MARGIN, slot_y, MARGIN + gw, slot_y)

      self.c.setFont(FONT_BOLD, 11)
      self.c.setFillColor(C_TEXT_DARK)
      day_str = f"{d.month:02d}.{d.day:02d} {WEEKDAYS_CN[d.weekday()]}"
      self.c.drawString(MARGIN + 5, slot_y + slot_h - 18, day_str)
      if self.inc_day:
        self.c.linkRect(
            "",
            f"dest_d_{d.month}_{d.day}",
            (MARGIN, slot_y + slot_h - 22, MARGIN + 90, slot_y + slot_h),
            Border="[0 0 0]",
        )

      self.draw_dot_grid(
          MARGIN + 100, slot_y + 2, gw - 100, slot_h - 10, spacing=11
      )
    self.c.showPage()

  def build_day_page(self, cur_date):
    m, d = cur_date.month, cur_date.day
    w_num = cur_date.isocalendar()[1]
    self.c.bookmarkPage(f"dest_d_{m}_{d}")
    self.draw_sidebar("day", m)

    self.c.setFont(FONT_BOLD, 20)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(
        MARGIN, PAGE_HEIGHT - 45, f"{m:02d}月{d:02d}日 {WEEKDAYS_CN[cur_date.weekday()]}"
    )

    if self.inc_week:
      self.c.setFont(FONT_REGULAR, 9)
      self.c.setFillColor(C_TEXT_MUTED)
      self.c.drawRightString(
          CONTENT_WIDTH, PAGE_HEIGHT - 42, f"第 {w_num} 週 ↗"
      )
      self.c.linkRect(
          "",
          f"dest_w_{w_num}",
          (
              CONTENT_WIDTH - 60,
              PAGE_HEIGHT - 50,
              CONTENT_WIDTH,
              PAGE_HEIGHT - 30,
          ),
          Border="[0 0 0]",
      )

    left_w = (CONTENT_WIDTH - MARGIN) * 0.42
    right_w = (CONTENT_WIDTH - MARGIN) * 0.58
    body_y = MARGIN + 10
    body_h = PAGE_HEIGHT - 85

    self.c.setStrokeColor(C_LINE)
    self.c.line(MARGIN + left_w, body_y, MARGIN + left_w, body_y + body_h)
    time_slots = list(range(8, 23))
    slot_h = body_h / len(time_slots)

    for idx, hour in enumerate(time_slots):
      line_y = body_y + body_h - (idx + 1) * slot_h
      self.c.setFont(FONT_REGULAR, 8)
      self.c.setFillColor(C_TEXT_MUTED)
      self.c.drawString(MARGIN + 5, line_y + slot_h - 10, f"{hour:02d}:00")
      self.c.setStrokeColor(C_LINE)
      self.c.line(MARGIN + 35, line_y, MARGIN + left_w - 10, line_y)

    rx = MARGIN + left_w + 15
    self.c.setFont(FONT_BOLD, 10)
    self.c.setFillColor(C_TEXT_DARK)
    self.c.drawString(rx, body_y + body_h - 12, "今日重點任務 (TASKS)")

    todo_rows = 10
    todo_slot_h = 24
    for i in range(todo_rows):
      ty = (body_y + body_h - 28) - (i + 1) * todo_slot_h
      self.c.setStrokeColor(C_BORDER)
      self.c.rect(rx, ty + 5, 10, 10, fill=0, stroke=1)
      self.c.setStrokeColor(C_LINE)
      self.c.line(rx + 18, ty + 5, rx + right_w - 20, ty + 5)

    notes_y = body_y
    notes_h = (body_y + body_h - 28) - todo_rows * todo_slot_h - body_y
    self.draw_dot_grid(rx, notes_y, right_w - 20, notes_h, spacing=11)
    self.c.showPage()

  def generate(self):
    if self.inc_annual:
      self.build_annual_page()
    if self.inc_month:
      for m in range(1, 13):
        self.build_month_page(m)
    if self.inc_week:
      cur = datetime.date(self.year, 1, 1)
      cur -= datetime.timedelta(days=cur.weekday())
      end = datetime.date(self.year, 12, 31)
      seen_weeks = set()
      while cur <= end:
        w_num = cur.isocalendar()[1]
        if w_num not in seen_weeks:
          seen_weeks.add(w_num)
          days = [cur + datetime.timedelta(days=i) for i in range(7)]
          self.build_week_page(w_num, days)
        cur += datetime.timedelta(days=7)
    if self.inc_day:
      cur = datetime.date(self.year, 1, 1)
      one_day = datetime.timedelta(days=1)
      while cur.year == self.year:
        self.build_day_page(cur)
        cur += one_day
    self.c.save()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--year", type=int, default=2026)
  parser.add_argument(
      "--annual", type=lambda x: (str(x).lower() == "true"), default=True
  )
  parser.add_argument(
      "--month", type=lambda x: (str(x).lower() == "true"), default=True
  )
  parser.add_argument(
      "--week", type=lambda x: (str(x).lower() == "true"), default=True
  )
  parser.add_argument(
      "--day", type=lambda x: (str(x).lower() == "true"), default=True
  )
  parser.add_argument("--output", type=str, default="planner.pdf")
  args = parser.parse_args()

  planner = KudrykvStylePlanner(
      args.output, args.year, args.annual, args.month, args.week, args.day
  )
  planner.generate()
