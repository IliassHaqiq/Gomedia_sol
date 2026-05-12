import React from 'react'
import './styles/ColorChart.css'

const colorData = [
  {
    name: 'Cyan-Blue',
    color: '#009ed7',
    cmyk: { C: 100, M: 0, Y: 0, K: 0 },
    rgb: { R: 0, G: 158, B: 215 },
    hex: '#009ED7'
  },
  {
    name: 'Magenta',
    color: '#ec608d',
    cmyk: { C: 0, M: 59, Y: 40, K: 7 },
    rgb: { R: 236, G: 96, B: 141 },
    hex: '#EC608D'
  },
  {
    name: 'Yellow',
    color: '#ffd700',
    cmyk: { C: 0, M: 16, Y: 100, K: 0 },
    rgb: { R: 255, G: 215, B: 0 },
    hex: '#FFD700'
  },
  {
    name: 'Black',
    color: '#1a1a1a',
    cmyk: { C: 0, M: 0, Y: 0, K: 90 },
    rgb: { R: 26, G: 26, B: 26 },
    hex: '#1A1A1A'
  },
  {
    name: 'Deep Teal',
    color: '#53b4ba',
    cmyk: { C: 54, M: 0, Y: 27, K: 27 },
    rgb: { R: 83, G: 180, B: 186 },
    hex: '#53B4BA'
  }
]

function ColorChart() {
  return (
    <div className="color-chart-container">
      <div className="color-chart">
        {colorData.map((item, index) => (
          <div key={index} className="color-row">
            {/* Color Circle */}
            <div className="color-circle-wrapper">
              <div
                className="color-circle"
                style={{ backgroundColor: item.color }}
              ></div>
            </div>

            {/* Data Table */}
            <div className="color-data-table">
              <div className="data-row">
                <div className="data-cell data-label">C</div>
                <div className="data-cell data-label">M</div>
                <div className="data-cell data-label">J</div>
                <div className="data-cell data-label">N</div>
              </div>
              <div className="data-row">
                <div className="data-cell">{item.cmyk.C}</div>
                <div className="data-cell">{item.cmyk.M}</div>
                <div className="data-cell">{item.cmyk.Y}</div>
                <div className="data-cell">{item.cmyk.K}</div>
              </div>
              <div className="data-row">
                <div className="data-cell data-label">R</div>
                <div className="data-cell data-label">V</div>
                <div className="data-cell data-label">B</div>
                <div className="data-cell data-label">Hex</div>
              </div>
              <div className="data-row">
                <div className="data-cell">{item.rgb.R}</div>
                <div className="data-cell">{item.rgb.G}</div>
                <div className="data-cell">{item.rgb.B}</div>
                <div className="data-cell">{item.hex}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ColorChart
