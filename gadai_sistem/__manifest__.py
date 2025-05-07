{
    "name": "Sistem Pegadaian",
    "version": "1.0",
    "category": "Custom",
    "summary": "Modul Pegadaian - Customer, Barang, dan Transaksi",
    "author": "Jajat Rohiman98",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "models/models_access.xml",
        "views/customer_views.xml",
        "views/barang_views.xml",
        "views/transaksi_views.xml"
    ],
    "installable": True,
    "application": True
}
