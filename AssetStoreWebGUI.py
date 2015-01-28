from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import cgi, webbrowser, AssetStoreAPI

class myHandler(BaseHTTPRequestHandler):
    
    STYLE = '''table{border-collapse:collapse;}td,th{border:1px gray solid;padding:5px;}th{background:#EEE;}
    .changelog_cell{position: relative;}
    .changelog_cell:hover .changelog_body {display: block;}
    .changelog_body {display: none;top: 0;right: 100%;width: 500px;position: absolute;padding: 5px;background: white;border: 2px solid gray;z-index: 1000;overflow: auto;}
    '''
    TEMPLATE = '<html><style>{style}</style><head></head><body>{body}</body></html>'
    
    def GenPubInfoHtml(self, client):
        publisherInfo = client.GetPublisherInfo()
        html = '<h2>Publisher info</h2><ul>'
        for k, v in publisherInfo.data.iteritems():
            html += '<li>%s: %s</li>'%(k.capitalize(),v)
        html += '</ul>'
        return html
    
    def GenSalesPeriodsHtml(self, client):
        salesPeriods = client.FetchSalesPeriods()
        html = '<h2>Sales periods</h2><ul>'
        for value in salesPeriods:
            html += '<li>Month: %d, year: %d, formatted: %s</li>' %(
                     value.GetMonth(), 
                     value.GetYear(),
                     datetime.fromtimestamp(value.GetDate()).strftime('%B %Y'))
        html += '</ul>'
        return html
    
    def GenSalesHtml(self, client, selectedPeriod):
        salesperiods = client.FetchSalesPeriods()
        try:
            salesyear, salesmonth = map(int, selectedPeriod.split('-'))
        except Exception:
            salesyear = salesperiods[0].GetYear()
            salesmonth = salesperiods[0].GetMonth()
        sales = client.FetchSales(salesyear, salesmonth)
        html = '<h2>Sales and Downloads</h2>'
        
        html += 'Period: <select name=\"selectedPeriod\" onChange=\"document.forms[\'asForm\'].submit();\">'
        for value in salesperiods:
            html += '<option value="%s" %s>%s</option>'%(
                str(value.GetYear())+'-'+str(value.GetMonth()),
                'selected' if (value.GetYear()==salesyear and value.GetMonth()==salesmonth) else '',
                datetime.fromtimestamp(value.GetDate()).strftime('%B %Y'))
        html += '</select><br/><br/>'
        
        html += '<h3>Sales</h3>'
        
        html += '<h3>Gross:$%s, net: $%s (%d%%)</h3>'%(sales.GetRevenueGross(), sales.GetRevenueNet(), sales.GetPayoutCut()*100)
        
        html += '<table><tr><th>Package Name</th><th>Price ($)</th><th>Qty</th><th>Refunds</th><th>Chargebacks</th><th>Gross ($)</th><th>First</th><th>Last</th></tr>'
        for value in sales.GetPackageSales():
            html += '<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(
                     value.GetShortUrl(),
                     value.GetPackageName(),
                     value.GetPrice(),
                     value.GetQuantity(),
                     value.GetRefunds(),
                     value.GetChargebacks(),
                     None if value.GetGross() == 0 else value.GetGross(),
                     None if value.GetFirstPurchaseDate() == None else datetime.fromtimestamp(value.GetFirstPurchaseDate()).strftime('%d %B %Y'),
                     None if value.GetLastPurchaseDate() == None else datetime.fromtimestamp(value.GetLastPurchaseDate()).strftime('%d %B %Y'))
        html += '</table>'
        
        html += '<h3>Free Downloads</h3>'
        downloads = client.FetchDownloads(salesyear, salesmonth)
        assetdownloads = downloads.GetPackageDownloads()
        if len(assetdownloads)>0:
            html += '<br/><table><tr><th>Package Name</th><th>Qty</th><th>First</th><th>Last</th></tr>'
            for value in assetdownloads:
                html += '<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>'%(
                         value.GetShortUrl(),
                         value.GetPackageName(),
                         value.GetQuantity(),
                         None if value.GetFirstDownloadDate() == None else datetime.fromtimestamp(value.GetFirstDownloadDate()).strftime('%d %B %Y'),
                         None if value.GetLastDownloadDate() == None else datetime.fromtimestamp(value.GetLastDownloadDate()).strftime('%d %B %Y'))
            html += '</table>'
        else:
            html += 'No Free Downloads available'
        return html
    
    def GenRevenueHtml(self, client):
        revenue = client.FetchRevenue()
        html = '<h2>Revenue</h2><table><tr><th>Date</th><th>Type</th><th>Description</th><th>Debit ($)</th><th>Credit ($)</th><th>Balance ($)</th></tr>'
        for value in revenue:
            infoType = 'Unknown'
            if value.GetInfoType()==AssetStoreAPI.RevenueInfo.TypeRevenue:
                infoType = 'Revenue'
            elif value.GetInfoType()==AssetStoreAPI.RevenueInfo.TypePayout:
                infoType = 'Payout'
            html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(
                     datetime.fromtimestamp(value.GetDate()).strftime('%B %Y'), 
                     infoType,
                     value.GetDescription(),
                     value.GetDebet() or '',
                     value.GetCredit() or '',
                     None if value.GetBalance()==0 else value.GetBalance())
        html += '</table>'
        return html
        
    def GenPendingHtml(self, client):
        packages = client.FetchPackages()
        html = '<h2>Packages</h2><table><tr><th>Package</th><th>Status</th><th>Version</th><th>Price ($)</th><th>Size</th><th>Created</th><th>Published</th><th>Modified</th><th>Id</th><th>Changelog</th></tr>'
        for package in packages:
            versions = package.GetVersions()
            html += "<tr>"
            for version in versions:
                status = version.GetStatus()
                if status==AssetStoreAPI.PackageVersionInfo.StatusPublished:
                    infoType = 'Published'
                elif status==AssetStoreAPI.PackageVersionInfo.StatusDraft:
                    infoType = 'Draft'
                elif status==AssetStoreAPI.PackageVersionInfo.StatusPending:
                    infoType = 'Pending'
                elif status==AssetStoreAPI.PackageVersionInfo.StatusDeclined:
                    infoType = 'Declined'
                elif status==AssetStoreAPI.PackageVersionInfo.StatusError:
                    infoType = 'Error'
                else:
                    infoType = 'Unknown'
                size = version.GetSize()
                html += '<td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s kB</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class=\"changelog_cell\"><i>Hover to see</i><div class=\"changelog_body\">%s</div></td>'%(
                        package.GetShortUrl(),
                        version.GetName(),
                        infoType,
                        version.GetVersion(),
                        version.GetPrice(),
                        size/1000,
                        datetime.fromtimestamp(version.GetCreatedDate()).strftime('%d %B %Y %H:%M:%S'),
                        datetime.fromtimestamp(version.GetPublishedDate()).strftime('%d %B %Y %H:%M:%S'),
                        datetime.fromtimestamp(version.GetModifiedDate()).strftime('%d %B %Y %H:%M:%S'),
                        package.GetId(),
                        version.GetReleaseNotes())
            html += "</hr>"
        html += '</table>'
        return html
    
    def GenInvoiceHtml(self, client, invoiceNumbers):
        html = '<h2>Verify invoice</h2>Enter comma separated invoice numbers:'
        html += '<input type=\"text\" name=\"invoiceNumbers\" value=\"%s\" size=\"13\">'%invoiceNumbers
        html += '<input type=\"submit\" value=\"Verify\">'
        if len(invoiceNumbers) > 0:
            html += '<table><tr><th>Invoice #</th><th>Package</th><th>Purchase</th><th>Refunded?</th></tr>'
            invoiceNumbersArray = invoiceNumbers.split(',')
            invoiceNumbersInfo = client.VerifyInvoice(invoiceNumbersArray)
            for value in invoiceNumbersInfo:
                html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(
                    value.GetInvoiceNumber(),
                    value.GetPackageName(),
                    datetime.fromtimestamp(value.GetPurchaseDate()).strftime('%d %B %Y'),
                    'Yes' if value.IsRefunded() else 'No')
            html += '</table>'
        return html
        
    def get_asset_store_data(self, postvars):
        #login
        store = AssetStoreAPI.AssetStoreClient()
        store.Login('publisher@example.com', 'password')	
        #Load HTML
        body = '<form action=\"#\" method=\"post\" id=\"asForm\">'
        body += self.GenPubInfoHtml(store)
        body += self.GenSalesPeriodsHtml(store)
        body += self.GenSalesHtml(store, postvars['selectedPeriod'][0] if postvars else '')
        body += self.GenRevenueHtml(store)
        body += self.GenPendingHtml(store)
        body += self.GenInvoiceHtml(store, postvars['invoiceNumbers'][0] if postvars else '')
        body += '</form>'
        html = self.TEMPLATE.format(style=self.STYLE, body=body)
        return html
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write(self.get_asset_store_data(None))
        return
    def do_POST(self):
        #Load post submission
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}
        #Send Response
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(self.get_asset_store_data(postvars))
        return

#Serve HTML
PORT_NUMBER = 8080
try:
    #Create a web server and define the handler to manage the incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    webbrowser.open("http://127.0.0.1:%d"%PORT_NUMBER)
    #Wait forever for incoming http requests
    server.serve_forever()
except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()
