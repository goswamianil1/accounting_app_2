import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def parse_xml_file(file_path: str) -> ET.Element:
    """Parse an XML file and return the root element."""
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Error parsing XML file {file_path}: {str(e)}")
        raise
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

def extract_master_data(root: ET.Element) -> Dict[str, List[Dict[str, Any]]]:
    """Extract master data (AccountGroups and Accounts) from MSAll.DAT XML."""
    data = {
        'account_groups': [],
        'accounts': []
    }
    
    try:
        # Extract Account Groups
        for group in root.findall(".//GROUP"):
            group_data = {
                'name': group.findtext('NAME', ''),
                'parent_name': group.findtext('PARENT', ''),
                'tmp_code': group.findtext('TMPCODE', ''),  # Temporary code for mapping
                'is_active': True
            }
            data['account_groups'].append(group_data)

        # Extract Accounts
        for account in root.findall(".//ACCOUNT"):
            account_data = {
                'name': account.findtext('NAME', ''),
                'code': account.findtext('CODE', ''),
                'group_name': account.findtext('GROUP', ''),
                'tmp_code': account.findtext('TMPCODE', ''),
                'gst_number': account.findtext('GSTIN', ''),
                'pan_number': account.findtext('INCOMETAXNUMBER', ''),
                'address': account.findtext('ADDRESS', ''),
                'is_active': True
            }
            data['accounts'].append(account_data)

    except Exception as e:
        logger.error(f"Error extracting master data: {str(e)}")
        raise

    return data

def extract_purchase_data(root: ET.Element) -> List[Dict[str, Any]]:
    """Extract purchase voucher data from Vh01042023.DAT XML."""
    vouchers = []
    
    try:
        for voucher in root.findall(".//VOUCHER"):
            if voucher.findtext('VCHTYPE', '') not in ['Purchase', 'Purchase Return']:
                continue

            voucher_data = {
                'voucher_number': voucher.findtext('VOUCHERNUMBER', ''),
                'date': voucher.findtext('DATE', ''),
                'voucher_type': 'PURCHASE' if voucher.findtext('VCHTYPE') == 'Purchase' else 'PURCHASE_RETURN',
                'party_name': voucher.findtext('PARTYNAME', ''),
                'narration': voucher.findtext('NARRATION', ''),
                'total_amount': float(voucher.findtext('TOTALAMOUNT', '0')),
                'net_amount': float(voucher.findtext('NETAMOUNT', '0')),
                
                # Nested entries
                'items': [],
                'bill_sundries': [],
                'account_entries': []
            }

            # Extract item entries
            for item in voucher.findall(".//ITEM"):
                item_data = {
                    'item_name': item.findtext('NAME', ''),
                    'quantity': float(item.findtext('QUANTITY', '0')),
                    'rate': float(item.findtext('RATE', '0')),
                    'amount': float(item.findtext('AMOUNT', '0')),
                    'hsn_code': item.findtext('HSNCODE', ''),
                    'gst_rate': float(item.findtext('GSTRATE', '0')),
                    'gst_amount': float(item.findtext('GSTAMOUNT', '0'))
                }
                voucher_data['items'].append(item_data)

            # Extract bill sundries
            for sundry in voucher.findall(".//BILLSUNDRY"):
                sundry_data = {
                    'name': sundry.findtext('NAME', ''),
                    'amount': float(sundry.findtext('AMOUNT', '0')),
                    'gst_rate': float(sundry.findtext('GSTRATE', '0')),
                    'gst_amount': float(sundry.findtext('GSTAMOUNT', '0'))
                }
                voucher_data['bill_sundries'].append(sundry_data)

            # Extract account entries
            for entry in voucher.findall(".//ACCOUNTENTRY"):
                entry_data = {
                    'account_name': entry.findtext('ACCOUNTNAME', ''),
                    'entry_type': 'DEBIT' if entry.findtext('DEBITAMOUNT') else 'CREDIT',
                    'amount': float(entry.findtext('DEBITAMOUNT') or entry.findtext('CREDITAMOUNT', '0')),
                    'narration': entry.findtext('NARRATION', '')
                }
                voucher_data['account_entries'].append(entry_data)

            vouchers.append(voucher_data)

    except Exception as e:
        logger.error(f"Error extracting purchase data: {str(e)}")
        raise

    return vouchers 