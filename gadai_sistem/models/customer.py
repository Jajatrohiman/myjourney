from odoo import models, fields

class GadaiCustomer(models.Model):
    _name = 'gadai.customer'
    _description = 'Data Pelanggan Pegadaian'

    name = fields.Char(string='Nama Pelanggan', required=True)
    nik = fields.Char(string='NIK', required=True)
    phone = fields.Char(string='Nomor Telepon')
    phone2 = fields.Char(string='Nomor Telepon 2')
    address = fields.Text(string='Alamat')
    transaksi_ids = fields.One2many('gadai.transaksi', 'customer_id', string='Transaksi')