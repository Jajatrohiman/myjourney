from odoo import models, fields

class InputData(models.Model):
    _name = 'input.data'
    _description = 'Model untuk Penginputan Data Sederhana'

    name = fields.Char(string='Nama', required=True)
    description = fields.Text(string='Deskripsi')
    date_input = fields.Datetime(string='Tanggal Input', default=fields.Datetime.now)
    barang = fields.Char(string='Barang', required=True)