function statusToClass(status) {
    switch (status) {
      case 'PENDING':
        return 'info';
      case 'PASS':
      case 'SUCCESS':
        return 'success'
      case 'FAIL':
      case 'FAILURE':
        return 'danger'
      default:
        return 'default'
    }
}