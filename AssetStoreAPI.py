import requests, datetime#, pytz

class AssetStoreException (Exception):
    pass

class AssetStoreClient(object):
    LOGIN_URL = 'https://publisher.assetstore.unity3d.com/login'
    LOGOUT_URL = 'https://publisher.assetstore.unity3d.com/logout'
    SALES_URL = 'https://publisher.assetstore.unity3d.com/sales.html'
    USER_OVERVIEW_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/user/overview.json'
    PUBLISHER_OVERVIEW_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher/overview.json'
    SALES_PERIODS_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/months/{publisher_id}.json'
    SALES_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/sales/{publisher_id}/{year}{month}.json'
    DOWNLOADS_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/downloads/{publisher_id}/{year}{month}.json'
    INVOICE_VERIFY_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/verify-invoice/{publisher_id}/{invoice_id}.json'
    REVENUE_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/revenue/{publisher_id}.json'
    PACKAGES_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/management/packages.json'
    API_KEY_JSON_URL = 'https://publisher.assetstore.unity3d.com/api/publisher-info/api-key/{publisher_id}.json'
    LOGIN_TOKEN = '26c4202eb475d02864b40827dfff11a14657aa41'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; rv:27.0) Gecko/20100101 Firefox/27.0'

    def __init__(self):
        self.loginToken = '';
        self.isLoggedIn = False;
        self.cookies = {};
        self.userInfoOverview = None;
        self.publisherInfoOverview = None;
            
    def LoginWithToken(self, token):
        self.AssertIsNotLoggedIn()
        self.loginToken = token
        self.isLoggedIn = True
        self.cookies['xunitysession'] = self.GetXUnitySessionCookie()

    def Login(self, username, password):
        self.AssertIsNotLoggedIn()
        token = self.GetLoginToken(username, password)
        self.LoginWithToken(token)
        return token
        
    def Logout(self):
        self.AssertIsLoggedIn()
        result = self.GetSimpleData({'url':self.LOGOUT_URL})
        self.AssertHttpCode('Logout failed, error code {code}', result.status_code);
        self.__init__() #resets the variables
    
    def IsLoggedIn(self):
        return self.isLoggedIn

    def GetUserInfo(self):
        self.AssertIsLoggedIn()

        if self.userInfoOverview == None:
            result = self.GetSimpleData({'url':self.USER_OVERVIEW_JSON_URL})
            self.AssertHttpCode('Fetching user data failed, error code {code}', result.status_code)
            self.userInfoOverview = result.json()

        return self.userInfoOverview

    def GetPublisherInfo(self):
        self.AssertIsLoggedIn()

        if self.publisherInfoOverview == None:
            result = self.GetSimpleData({'url':self.PUBLISHER_OVERVIEW_JSON_URL});
            self.AssertHttpCode('Fetching publisher data failed, error code {code}', result.status_code)
            publisherInfoObject = result.json()
            self.publisherInfoOverview = PublisherInfo(publisherInfoObject)

        return self.publisherInfoOverview
    
    def FetchApiKey(self):
        url = self.API_KEY_JSON_URL.format(publisher_id = self.GetPublisherInfo().GetId())
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching API key failed, error code {code}', result.status_code)
        keyDataObject = result.json()
        return keyDataObject['api_key']
    
    def FetchSalesPeriods(self):
        self.AssertIsLoggedIn()
        url = self.SALES_PERIODS_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId())
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching sales periods failed, error code {code}', result.status_code)
        salesPeriods = result.json()
        infoArray = []
        for value in salesPeriods['periods']:
            infoArray.append(SalesPeriod(value))
        return infoArray
        
    def FetchRevenue(self):
        self.AssertIsLoggedIn()
        url = self.REVENUE_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId())
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching sales periods failed, error code {code}', result.status_code)
        infoObject = result.json()
        infoArray = []
        for value in infoObject['aaData']:
            infoArray.append(RevenueInfo(value))
        return infoArray
        
    def FetchPackages(self):
        self.AssertIsLoggedIn()
        url = self.PACKAGES_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId())
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching packages failed, error code {code}', result.status_code)
        infoObject = result.json()
        infoArray = []
        for value in infoObject['packages']:
            infoArray.append(PackageInfo(value))
        return infoArray
    
    def VerifyInvoice(self, invoiceNumbers):
        from urllib import quote_plus
        self.AssertIsLoggedIn()
        invoiceNumbers = ','.join(invoiceNumbers)
        url = self.INVOICE_VERIFY_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId(), invoice_id=quote_plus(invoiceNumbers))
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Invoice verification failed, error code {code}', result.status_code)
        invoiceInfoObject = result.json()
        invoiceInfo = []
        for value in invoiceInfoObject['aaData']:
            invoiceInfo.append(InvoiceInfo(value))
        return invoiceInfo
        
    def FetchSales(self, year, month):
        self.AssertIsLoggedIn()
        year = int(year)
        month = int(month)
        if year<2010:
            raise AssetStoreException('Year must be after 2009')
        if month>12 or month<1:
            raise AssetStoreException('Month must be an integer between 1 and 12')
        month = str(month).zfill(2)
        year = str(year)
        url = self.SALES_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId(), year=year, month=month)
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching sales failed, error code {code}', result.status_code)
        salesInfoObject = result.json()
        salesInfo = []
        key = 0
        for value in salesInfoObject['aaData']:
            temp = {i:j for i,j in enumerate(value)}
            temp['shortUrl'] = salesInfoObject['result'][key]['short_url']
            salesInfo.append(PackageSalesInfo(temp))
            key+=1
        return PeriodSalesInfo(salesInfo, self.GetPublisherInfo().GetPayoutCut())
        
    def FetchDownloads(self, year, month):
        self.AssertIsLoggedIn()
        year = int(year)
        month = int(month)
        if year<2010:
            raise AssetStoreException('Year must be after 2009')
        if month>12 or month<1:
            raise AssetStoreException('Month must be an integer between 1 and 12')
        month = str(month).zfill(2)
        year = str(year)
        url = self.DOWNLOADS_JSON_URL.format(publisher_id=self.GetPublisherInfo().GetId(), year=year, month=month)
        result = self.GetSimpleData({'url':url})
        self.AssertHttpCode('Fetching downloads failed, error code {code}', result.status_code)
        downloadsInfoObject = result.json()
        downloadsInfo = []
        key = 0
        for value in downloadsInfoObject['aaData']:
            value['shortUrl'] = downloadsInfoObject['result'][key]['short_url']
            downloadsInfo.append(PackageDownloadsInfo(value))
            key += 1
        return PeriodDownloadsInfo(downloadsInfo)
        
    def SetupCurlQuery(self, params):
        pass
        
    def GetSimpleData(self, url):
        #Returns a requests.Response() instead of a dict
        self.AssertIsLoggedIn()
        if type(url)==dict: url=url['url']
        headers = {
                    'User-Agent':self.USER_AGENT,
                    'referer':self.LOGIN_URL
                    }
        r = requests.get(url, headers=headers, cookies=self.cookies)
        return r
        
    def GetXUnitySessionCookie(self):
        if self.isLoggedIn:
            return self.loginToken + self.LOGIN_TOKEN*2
        else:
            return self.LOGIN_TOKEN*3
            
    def GetLoginToken(self, username, password):
        query = {'user':username, 'pass':password, 'skip_terms':True}
        headers = {
                    'User-Agent':self.USER_AGENT,
                    'X-Unity-Session':self.GetXUnitySessionCookie(),
                    'referer':self.LOGIN_URL
                    }
        r = requests.post(self.LOGIN_URL, headers=headers, data=query)
        self.AssertHttpCode('Login failed, error code {code}', r.status_code)
        return r.text
        
    def AssertHttpCode(self, message, code):
        if HttpUtilities.IsErrorCode(code):
            raise AssetStoreException(message.format(code=code))
  
    def AssertIsLoggedIn(self):
        if not self.IsLoggedIn():
            raise AssetStoreException('Can\'t execute operation when not logged in')

    def AssertIsNotLoggedIn(self):
        if self.IsLoggedIn():
            raise AssetStoreException('Login already performed')

class ParsedData (object):
    def __init__(self):
        self.data = Array()
    def ParseDate(self, date):
        if date=='':
            return None
        import time, datetime
        timestamp = time.mktime(datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())
        return timestamp
        
    def ParseDateTime(self, dateTime):
        if dateTime=='':
            return None
        import time, datetime
        timestamp = time.mktime(datetime.datetime.strptime(dateTime, '%Y-%m-%d %H:%M:%S').timetuple())
        return timestamp
        
    def ParseCurrency(self, value):
        if value=='':
            return None
        return float(filter(lambda x: x.isdigit() or x in ',.-', value))
 
class PublisherInfo(object):
    def __init__(self, data):
        data = data['overview']
        self.data = {'id':int(data['id']),
                    'name':data['name'],
                    'description':data['description'],
                    'rating':int(data['rating']['average']),
                    'ratingCount':int(data['rating']['count']),
                    'payoutCut':data['payout_cut'],
                    'publisherUrl':data['long_url'],
                    'publisherShortUrl':data['short_url'],
                    'siteUrl':data['url'],
                    'supportUrl':data['support_url'],
                    'supportEmail':data['support_email']
                    }

    def GetId(self):
        return self.data['id']

    def GetName(self):
        return self.data['name']

    def GetDescription(self):
        return self.data['description']

    def GetRating(self):
        return self.data['rating']

    def GetRatingCount(self):
        return self.data['ratingCount']

    def GetPayoutCut(self):
        return self.data['payoutCut']

    def GetPublisherUrl(self):
        return self.data['publisherUrl']

    def GetPublisherShortUrl(self):
        return self.data['publisherShortUrl']

    def GetSiteUrl(self):
        return self.data['siteUrl']

    def GetSupportUrl(self):
        return self.data['supportUrl']

    def GetSupportEmail(self):
        return self.data['supportEmail']
    #Added method
    def __str__(self):
        return '\n'.join(k+': '+str(self.data[k]) for k in self.data.keys())
        
class RevenueInfo (ParsedData):
    TypeUnknown = -1;
    TypeRevenue = 1;
    TypePayout = 2;
    
    def __init__(self, data):
        infoType = self.TypeUnknown;
        if 'revenue' in data[1]:
            infoType = self.TypeRevenue
        elif 'payout' in data[1]:
            infoType = self.TypePayout
        self.data = {
            'date':self.ParseDate(data[0]),
            'description':data[1],
            'debet':self.ParseCurrency(data[2]),
            'credit':self.ParseCurrency(data[3]),
            'balance':self.ParseCurrency(data[4]),
            'infoType':infoType
            }
    def GetDate(self):
        return self.data['date']
    def GetDescription(self):
        return self.data['description']
    def GetDebet(self):
        return self.data['debet']
    def GetCredit(self):
        return self.data['credit']
    def GetBalance(self):
        return self.data['balance']
    def GetInfoType(self):
        return self.data['infoType']

class InvoiceInfo (ParsedData):
    def __init__(self, data):
        self.data = {
            'id':data[0],
            'packageName':data[1],
            'date':self.ParseDate(data[2]),
            'isRefunded':data[3] == 'Yes',
        }
    def GetInvoiceNumber(self):
        return self.data['id']
    def GetPackageName(self):
        return self.data['packageName']
    def GetPurchaseDate(self):
        return self.data['date']
    def IsRefunded(self):
        return self.data['isRefunded']
class SalesPeriod(object):
    def __init__(self, data):
        self.year = int(data['value'][0:4])
        self.month = int(data['value'][4:6])
    def GetYear(self):
        return self.year
    def GetMonth(self):
        return self.month
    def GetDate(self):
    	import datetime, time
    	return time.mktime(datetime.datetime(self.year, self.month, 1, 0, 0, 0, 0).timetuple())
        
class PeriodSalesInfo(object):
    def __init__(self, packageSales, payoutCut = 0.7):
        self.packageSales = packageSales
        self.payoutCut = float(payoutCut)
        self.revenueGross = 0
        for value in self.packageSales:
            self.revenueGross += value.GetPrice() * (value.GetQuantity() - value.GetRefunds() - value.GetChargebacks())
        self.revenueNet = self.revenueGross * self.payoutCut
    def GetPackageSales(self):
        return self.packageSales
    def GetRevenueGross(self):
        return self.revenueGross
    def GetRevenueNet(self):
        return self.revenueNet
    def GetPayoutCut(self):
        return self.payoutCut

class PeriodDownloadsInfo(object):
    def __init__(self, packageDownloads):
        self.packageDownloads = packageDownloads
    def GetPackageDownloads(self):
        return self.packageDownloads
        
class PackageSalesInfo (ParsedData):
    def __init__(self, data):
        self.data = {
            'name':data[0],
            'price':self.ParseCurrency(data[1]),
            'quantity': None if data[2] == None else int(data[2]),
            'refunds': None if data[3]==None else abs(int(data[3])),
            'chargebacks': None if data[4]==None else abs(int(data[4])),
            'gross': None if data[5]=='' else self.ParseCurrency(data[5]),
            'firstPurchase': None if data[6]=='' else self.ParseDate(data[6]),
            'lastPurchase': None if data[7] == None else self.ParseDate(data[7]),
            'shortUrl':data['shortUrl'],
            }

    def GetPackageName(self):
        return self.data['name']

    def GetPrice(self):
        return self.data['price']

    def GetQuantity(self):
        return self.data['quantity']

    def GetRefunds(self):
        return self.data['refunds']

    def GetChargebacks(self):
        return self.data['chargebacks']

    def GetGross(self):
        return self.data['gross']

    def GetFirstPurchaseDate(self):
        return self.data['firstPurchase']

    def GetLastPurchaseDate(self):
        return self.data['lastPurchase']

    def GetShortUrl(self):
        return self.data['shortUrl']

    def FetchPackageId(self):
        redirect = HttpUtilities.GetRedirectUrl(self.data['shortUrl'])
        redirect = end(explode('/', redirect))
        return redirect

class PackageDownloadsInfo(object):
    def __init__(self, data):
        self.data = {
            'name':data[0],
            'quantity':int(data[1]) if data[1] != None else None,
            'firstDownload':self.ParseDate(data[2]) if data[2] != None else None,
            'lastDownload':self.ParseDate(data[3]) if data[3] != None else None,
            'shortUrl':data['shortUrl'],
        	}
    def GetPackageName(self):
        return self.data['name']
    def GetQuantity(self):
        return self.data['quantity']
    def GetFirstDownloadDate(self):
        return self.data['firstDownload']
    def GetLastDownloadDate(self):
        return self.data['lastDownload']
    def GetShortUrl(self):
        return self.data['shortUrl']
    def FetchAssetId(self):
        redirect = HttpUtilities.GetRedirectUrl(self.data['shortUrl'])
        redirect = end(explode('/', redirect))
        return redirect
class PackageVersionInfo(ParsedData):
    StatusUnknown = -1
    StatusError = 1
    StatusDraft = 2
    StatusPending = 3
    StatusDeclined = 4
    StatusPublished = 5
    def __init__(self, data):
        status = self.StatusUnknown
        # Parse status
        if 'published' in data['status']:
            status = self.StatusPublished
        elif 'pending' in data['status']:
            status = self.StatusPending
        elif 'declined' in data['status']:
            status = self.StatusDeclined
        elif 'draft' in data['status']:
            status = self.StatusDraft
        elif 'error' in data['status']:
            status = self.StatusError
        self.data = {
            'name':data['name'],
            'status':status,
            'size': int(data['size']),
            'modifiedDate': self.ParseDateTime(data['modified']),
            'createdDate': self.ParseDateTime(data['created']),
            'publishedDate': self.ParseDateTime(data['published']),
            'price': float(data['price']),
            'version': data['version_name'],
            'categoryId': int(data['category_id']),
            'releaseNotes': data['publishnotes']
        	}
    def GetName(self):
        return self.data['name']
    def GetStatus(self):
        return self.data['status']
    def GetVersion(self):
        return self.data['version']
    def GetSize(self):
        return self.data['size']
    def GetPrice(self):
        return self.data['price']
    def GetCategoryId(self):
        return self.data['categoryId']
    def GetReleaseNotes(self):
        return self.data['releaseNotes']
    def GetModifiedDate(self):
        return self.data['modifiedDate']
    def GetCreatedDate(self):
        return self.data['createdDate']
    def GetPublishedDate(self):
        return self.data['publishedDate']
        
class PackageInfo(ParsedData):
    def __init__(self, data):
        versions = []
        for versionData in data['versions']:
            versions.append(PackageVersionInfo(versionData))
        self.data = {
            'id': int(data['id']),
            'shortUrl': data['short_url'],
            'versions': versions
            }
    def GetId(self):
        return self.data['id']
    def GetShortUrl(self):
        return self.data['shortUrl']
    def GetVersions(self):
        return self.data['versions']

class HttpUtilities (object):
    errorMessages = {
        # [Informational 1xx]    
        100:'Continue',    
        101:'Switching Protocols',    
        # [Successful 2xx]    
        200:'OK',    
        201:'Created',    
        202:'Accepted',    
        203:'Non-Authoritative Information',    
        204:'No Content',    
        205:'Reset Content',    
        206:'Partial Content',    
        # [Redirection 3xx]    
        300:'Multiple Choices',    
        301:'Moved Permanently',    
        302:'Found',    
        303:'See Other',    
        304:'Not Modified',    
        305:'Use Proxy',    
        306:'(Unused)',    
        307:'Temporary Redirect',    
        # [Client Error 4xx]    
        400:'Bad Request',    
        401:'Unauthorized',    
        402:'Payment Required',    
        403:'Forbidden',    
        404:'Not Found',    
        405:'Method Not Allowed',    
        406:'Not Acceptable',    
        407:'Proxy Authentication Required',    
        408:'Request Timeout',    
        409:'Conflict',    
        410:'Gone',    
        411:'Length Required',    
        412:'Precondition Failed',    
        413:'Request Entity Too Large',    
        414:'Request-URI Too Long',    
        415:'Unsupported Media Type',    
        416:'Requested Range Not Satisfiable',    
        417:'Expectation Failed',    
        # [Server Error 5xx]    
        500:'Internal Server Error',    
        501:'Not Implemented',    
        502:'Bad Gateway',    
        503:'Service Unavailable',    
        504:'Gateway Timeout',    
        505:'HTTP Version Not Supported'
        }

    @classmethod
    def IsErrorCode(self, code):
        # Error codes begin at 400
        return type(code)==int and code >= 400
        
    @classmethod
    def GetStatusMessage(self, code):
        return self.errorMessages[code]
    
    @classmethod
    def GetRedirectUrl(self, url):
        return requests.get(url).url
